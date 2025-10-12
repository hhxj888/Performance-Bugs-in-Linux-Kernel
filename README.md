# Performance-Bugs-in-Linux-Kernel

This is the open-source repository for the paper titled **"Demystifying Performance Bugs in Large-Scale Infrastructure Software: A Comprehensive Study on Distribution, Root Causes, and Detection in the Linux Kernel."**

The repository consists of two main parts: the dataset and the scripts.

## Overall Structure

```
|____dataset
|    |____Linux_Performance_Commit_Dataset.json
|____README.md
|____scripts
|    |____features_extracted_by_baseline_method.csv
|    |____llm_config
|         |____CodeLlama-7b-hf.yaml
|         |____llama3.yaml
|         |____starcoder7.yaml
|         |____gemma2.yaml
|         |____deepseek_chat_16b.yaml
|         |____glm4.yaml
|         |____Mistral-7B.yaml
|         |____qwen2.yaml
|         |____Phi-3-Medium.yaml
|         |____codegemma.yaml
|         |____starcoder15.yaml
|         |____CodeQwen.yaml
|         |____llama3.1.yaml
|         |____Phi-3-mini.yaml
|         |____deepseek_coder_16b.yaml
```

- The dataset, `Linux_Performance_Commit_Dataset.json`, is the **Real-world performance bug dataset (LPC)** collected and curated in the paper.
- The file `baseline_feature.csv` provides the features extracted for RQ4 (Research Question 4) as required for the baseline, with detailed methodology referenced in the paper **"Enhancing Performance Bug Prediction Using Performance Code Metrics"** and its corresponding open-source repository: https://github.com/NintyFive/MSR2024-Replication-Package

## Model Training Dependencies

- The repository depends on **LLaMA-Factory** for model training.
- The directory `llm_config` contains configuration files for each model used in the training, such as **CodeLlama-7b-hf.yaml**, **llama3.yaml**, and others.