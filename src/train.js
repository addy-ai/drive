/*
// Source Data is either provided as {data}, retrieved via {path} , or using a service object { classInstance, query }
// The data provided is expected to be an array. {value} is optional and points to the  location of our data from the source Data
//
// ARGS:
// 
// input - {path, data, classInstance, query: {} } - Required for Service info, Optional way to specify Path/Data attributes
// inputData - [data] - Actaul Final Data - no Value use Needed
// inputPath - "path to csv" - Required if 'input' service object nor 'inputData' is provided  
// inputValue - csvColumnName or QueryObjProperty - Optional, specified a column or attribute from the dataset provided to use as the inputData.
//
*/
// import Papa from 'papaparse'; // CSV Parser

const { type } = require('os'); 
// require readline for manipulating stdin and stdout streams
const readline = require('readline');

class Train {
  constructor(props) {
    const { verbose, ...train } = props;
    this.verbose = verbose || false;

    // Set Inputs
    const i = props.input || {};
    this.inputData = props.inputData || i.data || props.data || false
    this.inputPath = props.inputPath || i.path || props.path || false
    this.inputService = props.inputService || i.service || props.service || false // Config
    this.inputQuery = props.inputQuery || i.query || props.query || false
    this.inputValue = props.inputValue || i.value || 'input'

    // Set Output
    const o = props.output || {};
    this.outputData = props.outputData || o.data || props.data || false
    this.outputPath = props.outputPath || o.path || props.path || false  // !data & !service user input 
    this.outputService = props.outputService || o.service || props.service || false // !data & !path user input 
    this.outputQuery = props.outputQuery || o.query || props.query || false //
    this.outputValue = props.outputValue || o.value || 'output'
    this.trainPath = props.trainPath || false
    this.deploy = props.deploy || false
  }

  // Initialize the class
  static async init(config) {
    if (config.verbose) console.log('DriveTrain init()');
    if (typeof (config) !== 'object') { return }
    let trainer = new Train(config);
    let { inp, out } = await trainer.prepareData();
    return trainer
  }
  
  async trainModel(additionalConfigInfo) { 
    if (this.verbose) { console.log('DriveTrain:trainModel()'); }
    /*
    X - Format ingested data from emails & firestore into JSON of {input,output}
    X - Grab all required params from YAML
    ? - Make API call to python repo in GCP to fine tune 		-> using req params  ->  Our private one... unless they deploy the build themselves.
    ? - In python repo, convert the JSON training data to CSV 	-> 
    ? - Save the CSV in DEV-120 to a folder in the repo path	-> This is funny.
    ? - Reference the CSV file in training
    ? - Delete the training CSV after training is complete, 
    ? - do this in the fask api method
    */ 

    // Get the right training env. Create it if required.
    let trainPath = huggingfaceInfo.hfTrainPath || this.trainPath
    if(!trainPath.includes('http')){
      // Create a new training huggingface repository
      console.log('\nCreating or updating space...');
      const HuggingFace = require('../src/huggingFace');
      const hf = new HuggingFace(process.env.HUGGINGFACE_API_KEY); 
      await hf.createOrUpdateSpace(trainPath, this.isPrivate || additionalConfigInfo.isPrivate);
      trainPath = `https://${trainPath.replace('/','-')}.hf.space`; 
    }
    else{ 
      trainpath = 'https://api.langdrive.ai/train' 
    }
    console.log('trainPath', trainPath) 
    // data = inp || this.data
    // console.log('Train:trainModel:huggingfaceInfo', huggingfaceInfo)
    // console.log('DriveTrain:trainModel()', this.data); 
    let sendThis = {
      "baseModel": huggingfaceInfo?.baseModel || "vilsonrodrigues/falcon-7b-instruct-sharded",
      "trainingData": this.data,
      "hfToken": huggingfaceInfo.hfToken,
      "deployToHf": this.deploy || huggingfaceInfo.deployToHf,
      "hfModelPath": huggingfaceInfo.hfModelPath,                             // where to save the fine tuned model
    }
    let trainingService = huggingfaceInfo?.trainingService || 'https://api.langdrive.ai/train'
    // console.log('Train:trainModel:sendThis', sendThis.trainingData) 
    let model = await fetch(trainingService, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sendThis)
    })
    console.log('trainModel:sentthis:', {
      sendThis
    })
    return model
  }

  // Retrieve the data needed
  async prepareData() {
    if (this.verbose) console.log('DriveTrain:PrepareData()'); 
    let inp = this.input = await this.getData('input');
    let out = this.output = await this.getData('output'); 

    // console.log('DriveTrain:PrepareData:inp', inp, out)

    // create a new array of objects with the input and output data
    let data = this.data = inp.map((input, i) => { return { input: inp[i], output: out[i] } })

    // this.verbose && console.log(`DriveTrain:PrepareData:FIN`,this.input, this.output)
    return data
  }

  // Source type 1
  async getDataFromUrl(url) {
    // console.log('Train:prepareData:getDataFromUrl')
    try {
      let data;
      // User provided a relative link to a local file
      if (!url.startsWith('http')) { 
        const fs = require('fs');
        data = await fs.promises.readFile(url, 'utf8');
      }
      // User provided a URL to a remote file
      else {
        const response = await fetch(url);
        if (!response.ok) { 
          throw new Error('Network response was not ok'); 
        }
        data = await response.text();
      } 
      const parseCsv = require("./utilsNode").parseCsv; 
      // console.log('Train:prepareData:getDataFromUrl:Parsing')
      let finData = parseCsv(data)
      return finData 
    } catch (error) {
      throw new Error(`Error retrieving data: ${error.message}`);
    }
  } 
  

  // Source type 2
  async getDataFromService(classInstance, query) {
    this.verbose && console.log('DriveTrain:prepareData:getDataFromService:START')
    let classMethodName = Object.keys(query)[0]
    let fn = classInstance[classMethodName]
    // console.log('DriveTrain:prepareData:getDataFromService:MID', {classMethodName, fn, query})
    let getOrderedFnArgNames = (func) => { // Returns Class Method Parameters in Order of Declaration
      const fnStr = func.toString().replace(/((\/\/.*$)|(\/\*[\s\S]*?\*\/))/mg, '');
      const result = fnStr.slice(fnStr.indexOf('(') + 1, fnStr.indexOf(')')).match(/([^\s,]+)/g);
      return result === null ? [] : result;
    } 
    let args = getOrderedFnArgNames(fn).map((paramName) => query[classMethodName][paramName])
    args = args[0] != undefined && args || [query[classMethodName]] 
    let data = await Promise.resolve(classInstance[classMethodName](...args)) // Preserve 'this'   
    // console.log('DriveTrain:getDataFromService:END',{data})
    return data
  }
  // Handle the optional 'value' parameter from Source Data
  getValuesFromData(data, value) { 
    if (!value) { return data }
    // console.log(!!value, value, value=='',typeof(value) )     
    if (value === '*') { return data } 
    else {
      // Iterate through each row and retrieve the value
      // console.log(value,'GET VALUES FROM DATA', data[0], value) 
      return data.map((row) => {
        try{
          if (value.includes('.')) {
          return value.split('.').reduce((obj, key) => obj ? obj[isNaN(key) ? key : parseInt(key)] : undefined, row);
        }
        return row[value]
        }
        catch(err){
          console.log('getValuesFromData:err', err)
          return false
          // return JSON.stringify(row)
        }
      })
    }
  }

  // Retrieves data and handles the optional 'value' parameter
  async getData(lbl) { 
    this.verbose && console.log(`DriveTrain:getData: ${lbl}`)

    let path = this[`${lbl}Path`]
    let service = this[`${lbl}Service`]
    let query = this[`${lbl}Query`]
    let data = this[`${lbl}Data`]
    let value = this[`${lbl}Value`]

    // console.log('getData: ', {path, service, query, data, value}) 

    // Get raw Data from URL 
    if (!data && path) { data = await this.getDataFromUrl(path); }
    // Get raw Data from Service   
    else if (!data && service && query) { data = await this.getDataFromService(service, query) } 
    // Retrieve Data from raw Data  
    let extractedData = this.getValuesFromData(data, value)  
    // console.log('getData:extractedData', extractedData)
    return extractedData
  }
}
module.exports = Train;

// FOR NOTES: 
// default == 'input' or 'output'
// if (value === '*') { return data }
// We dont have a service to work with local files atm.
// for csvs set 'csv' as service (optionally,atm) and 'path' as path (required)
// be explicitly clear that the cli args overwrite the yaml file.
