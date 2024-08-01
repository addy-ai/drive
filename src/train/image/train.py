# Import the necessary modules and set environment variables

print('train1')
import json
import os
from pprint import pprint
import bitsandbytes as bnb
import torch
import torch.nn as nn
import transformers
print('train2')
from datasets import (
    load_dataset,
    Dataset
)
from peft import (
    LoraConfig,
    PeftConfig,
    PeftModel,
    get_peft_model,
    prepare_model_for_kbit_training
)
from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig
)


from huggingface_hub import HfFolder, _login

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

"""
Train LLMs
"""


class LLMTrain:
    # Initialize the class with model and data path
    def __init__(self, MODEL_NAME, training_data, hf_token) -> None:
        self.MODEL_NAME = MODEL_NAME
        self.training_data = training_data
        self.HUGGINGFACE_TOKEN = hf_token
        # os.environ['HF_HOME'] = '/content'  # Sets the Hugging Face cache directory

        if 'HF_HOME' in os.environ:
            print("HF_HOME:", os.environ['HF_HOME'])
        else:
            print("HF_HOME environment variable is not set.")

        os.environ.pop('HF_HOME', None)  # Remove HF_HOME if it exists

        os.environ['HUGGINGFACE_HUB_TOKEN'] = hf_token
        HfFolder.save_token(hf_token)

        self.check_if_hugging_face_token_is_set()

    # Method to create transformer model and tokenizer
    def create_model_and_tokenizer(self):
        # Define Quantization configuration to optimize model

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        # Create Transformer model based on given model name
        model = AutoModelForCausalLM.from_pretrained(
            self.MODEL_NAME,
            device_map="auto",
            trust_remote_code=True,
            quantization_config=bnb_config
        )
        # Create a tokenizer for the designated model
        tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        tokenizer.pad_token = tokenizer.eos_token
        self.tokenizer = tokenizer
        return model, tokenizer

    # Method to prepare and configure the model for training
    def prepare_and_configure_model(self, model):
        model.gradient_checkpointing_enable()
        model = prepare_model_for_kbit_training(model)
        # Define Configuration for LoRa (Long Range Transformers)
        config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["query_key_value"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        # Apply the defined configuration to the model
        model = get_peft_model(model, config)
        self.print_trainable_parameters(model)
        return model

    # Method to generate result based on user provided prompt
    def generate_future_with_prompt(self, model, tokenizer, prompt):
        generation_config = model.generation_config

        generation_config.max_new_tokens = 200
        generation_config.temperature = 0.7
        generation_config.top_p = 0.7
        generation_config.num_return_sequences = 1
        generation_config.pad_token_id = tokenizer.eos_token_id
        generation_config.eos_token_id = tokenizer.eos_token_id

        device = "cuda:0"
        # Encoding the prompt using tokenizer
        encoding = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.inference_mode():
            outputs = model.generate(
                input_ids=encoding.input_ids,
                attention_mask=encoding.attention_mask,
                generation_config=generation_config
            )
        print("Decoded: ", tokenizer.decode(
            outputs[0], skip_special_tokens=True))

    """
    Method to load and tokenize the dataset
    It expects an array of object each object of the format:
    {
        'input': '{{user_input}}',
        'output': '{{model_output}}'
    }
    """

    def load_training_data(self, data):
        # Convert array of objects to dictionary format
        data_dict = {
            'input': [obj['input'] for obj in data],
            'output': [obj['output'] for obj in data]
        }
        d = Dataset.from_dict(data_dict)
        d = d.shuffle().map(self.generate_and_tokenize_prompt)
        return d

    # Method to fine tune the model
    def fine_tune_model(self, model, data, tokenizer, deploy_to_hf, hf_token, hub_model_id, model_path):
        training_args = transformers.TrainingArguments(
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            num_train_epochs=1,
            learning_rate=2e-4,
            fp16=True,
            save_total_limit=3,
            logging_steps=1,
            output_dir="experiments-1",
            overwrite_output_dir=True,
            optim="paged_adamw_8bit",
            lr_scheduler_type="cosine",
            warmup_ratio=0.05,

            # should_save=deploy_to_hf,
            # push_to_hub=deploy_to_hf,

            hub_model_id=hub_model_id,
            hub_token=hf_token,
        )
        trainer = transformers.Trainer(
            model=model,
            train_dataset=data,
            args=training_args,
            data_collator=transformers.DataCollatorForLanguageModeling(
                tokenizer, mlm=False),
        )

        return trainer

    # Run a complete training cycle
    def run_train(self, MODEL_NAME, training_data, deploy_to_hf, hf_token, model_path):
        self.MODEL_NAME = MODEL_NAME
        model, tokenizer = self.create_model_and_tokenizer()
        model = self.prepare_and_configure_model(model)
        prompt = """
        <human>: midjourney prompt for a girl sit on the mountain
        <assistant>:
        """.strip()

        self.generate_future_with_prompt(model, tokenizer, prompt)
        data = self.load_training_data(training_data)

        push_to_hub_model_id = ""

        if model_path and "/" in model_path:
            push_to_hub_model_id = model_path.split(
                "/")[1]  # Get everything after the first "/"

        trainer = self.fine_tune_model(
            model, data, tokenizer, deploy_to_hf, hf_token, push_to_hub_model_id, model_path)
        model.config.use_cache = False

        trainer.train()

        # Deploy model to Hugging Face Model Hub if necessary
        if (deploy_to_hf and self.check_if_hugging_face_token_is_set()):
            # Trainer push to hub
            trainer.model.push_to_hub(model_path)
            print("Successfully deployed to hub", model_path)
            return True

        # If everything went well, return true
        return True

    # Method to save and push the trained model to Hugging Face Model Hub

    def deploy_to_hugging_face(self, model, model_path, hf_token):
        model.save_pretrained("trained-model")
        PEFT_MODEL = model_path
        model.push_to_hub(PEFT_MODEL, use_auth_token=True)

    def check_if_hugging_face_token_is_set(self):
        # Get the path to the token file
        token_file = HfFolder.path_token

        print("Token file path:", token_file)

        # Check if the token file exists and read its content
        if os.path.isfile(token_file):
            with open(token_file, 'r') as file:
                saved_token = file.read().strip()
                print("Token found:", saved_token)
                return True
        else:
            print("No token found.")
            return False

    # Generate dialog prompt with human and assistant tags
    def generate_prompt(self, data_point):
        return f"""
        <human>: {data_point["input"]}
        <assistant>: {data_point["output"]}
        """.strip()

    # Tokenize the generated dialog prompt
    def generate_and_tokenize_prompt(self, data_point):
        full_prompt = self.generate_prompt(data_point)

        # padding and truncation are set to True for handling sequences of different length.
        tokenized_full_prompt = self.tokenizer(
            full_prompt, padding=True, truncation=True)

        return tokenized_full_prompt

    # Print the number of parameters that are trainable in the model
    def print_trainable_parameters(self, model):
        """
        Prints the number of trainable parameters in the model.
        """
        trainable_params = 0
        all_param = 0

        for _, param in model.named_parameters():
            all_param += param.numel()  # Total parameters
            if param.requires_grad:
                trainable_params += param.numel()  # Trainable parameters
        print(
            f"trainable params: {trainable_params} || all params: {all_param} || trainables%: {100 * trainable_params / all_param}"
        )

    def generate_download_url(base_url, folder_path, token=None):
        """
        Generates a URL for the download endpoint.

        :param base_url: The base URL of the server (e.g., 'http://yourserver.com')
        :param folder_path: The path to the folder to be downloaded.
        :param token: Optional authentication token.
        :return: The complete URL for downloading the folder.
        """
        from urllib.parse import quote

        # URL encode the folder path
        encoded_path = quote(folder_path)

        # Construct the URL
        url = f"{base_url}/download/{encoded_path}"

        # Add the token to the query string if provided
        if token:
            url += f"?token={token}"

        return url
