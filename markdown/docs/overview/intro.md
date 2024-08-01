# Introduction

## Welcome to Langdrive's Documentation Portal!

Langdrive: Easily train and deploy your favorite models. 

There are many ways to train and develop LLMs with LangDrive - One way is to configure a [YAML](./yaml.md) doc and by issuing a [CLI](./cli.md) command. Another way would be importing it as a class modules within a project of your own, YAML doc optional. 

Whether you're a beginner or an experienced developer, our Data Connectors and LLM tools empower you to build, integrate, and deploy with confidence. Data  Connectors help source data from third parties (email, firestore, gdrive) and prepare it for your models. When it comes to training, hosting, and deploying models (Locally, Huggingface, SageMaker, CloudRun), our LLM tools have you covered. All of this is readily available from CLI arguements, a YAML doc, or directly in-code. 

LangDrive, built specifically for Node.js, makes training and deploying AI models effortless. We provide a library that facilitates data connection and automates training and deployment, ensuring your projects are easy to manage and scale.

Read our [Getting Started](./gettingStarted.md) page to jump right in or browse our documentation using the nav below.

## [Data Connectors Overview](./api/dataOverview.md)
Get to grips with classes that help you fetch and process data. This includes `Firestore` for database interactions, `Google Drive` for file management, and `EmailRetriever` for fetching emails. 

### [Google Drive](./api/gdrive.md)
This section provides a comprehensive look at its constructor, various methods, and how it leverages Google APIs for file operations and authentication. Explore how `DriveUtils` enhances your Google Drive experience with functionalities covering file listing, information retrieval, and file management.

#### [Firestore](./api/firestore.md)
Designed for robust interaction with Firebase Firestore, learn about its constructor, key methods, and how it can enhance your database interactions.

#### [EmailRetriever](./api/email.md)
Tailored for retrieving emails from different email clients using SMTP configurations, discover its constructor, key methods, and additional features.

## [LLM Overview](./api/llmOverview.md)
Training and deploying LLMs require resources most of us do not have. That is where our `HuggingFace`, `HerokuHandler`, and `utils` class come into play. These set of classes fascilitate the training and deployment of your LLM. 

#### [HuggingFace](./api/huggingFace.md)
Explore the `HuggingFace` class, your gateway to interacting with the Hugging Face API. Learn about its constructor, key methods, and how it can simplify your AI-driven tasks.

#### [HerokuHandler](./api/heroku.md)
Understand the `HerokuHandler` class, which simplifies interactions with the Heroku API. This overview covers its constructor, key methods, and how it can enhance your Heroku experience.

#### [Chatbot](./api/chatbot.md)
Discover the `DriveChatbot`, a demonstration and testing tool for Async Promises in chatbot interactions. Google [OAuth2](https://developers.google.com/identity/protocols/oauth2) keys are required to run your own instance. Read our tutorial on OAuth2 on our [blog](https://addy.beehiiv.com/).

#### [Utils](./api/utils.md)
Understand the essential Node.js script for deploying machine learning models, including its main functions, modules, and how it utilizes various libraries for file operations and environment management. Includes CLI utils.

#### [Training](./api/train.md)
This section covers its constructor, key methods, and how it streamlines the training process of your models.

## Contributing

Interested in contributing to LangDrive? Check out our [contributing guide](https://pages.github.io/addy-ai/langdrive/contributors.md).

---

Navigate through our sections to find comprehensive guides and insights that suit your development needs!

