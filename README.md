# Cross-modal Search for E-commerce: Building and Scaling a Cross-Modal Image Retrieval App

Read [blog post](https://www.anyscale.com/blog/cross-modal-search-for-e-commerce-building-and-scaling-a-cross-modal-image-retrieval-app) about the project.

![](https://technical-training-assets.s3.us-west-2.amazonaws.com/Anyscale-generic/blog/overview-blog.png)

## 1. Quickstart

### Register or login to Anyscale

If you don't have an Anyscale account, you can register [here](https://console.anyscale.com/register/ha?utm_source=github&utm_medium=github&utm_content=cross-modal-search-ecommerce-project).

If you already have an account, [login](https://console.anyscale.com/v2?utm_source=github&utm_medium=github&utm_content=cross-modal-search-ecommerce-project) here.

### Prepare Anyscale Workspace 

#### Step 1

Once you are logged in, go to workspaces by clicking the "**Workspaces**" tab on the left side of the home screen:

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/workspaces-tab.png" width="800px">

#### Step 2

Create a new workspace by clicking the "**Create Workspace**" button:

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/workspace-create.png" width="800px">

#### Step 3

Specify Workspace details as displayed below and click "**Create**":

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/workspace-form-v2.png" width="800px">

#### Step 4

Wait for the workspace to be created:

*(this can take up to one minute)*

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/workspace-creation.png" width="800px">  

> [!NOTE]
> Your workspace is ready!

#### Step 5

Open the terminal in the workspace and clone the repository by running the following command:

```bash
git clone https://github.com/anyscale/cross-modal-search-ecommerce-project.git
```

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/workspace-terminal.png" width="800px">

#### Step 6

Go to the project directory:

```bash
cd cross-modal-search-ecommerce-project
```

## 2. Set up Pinecone

You'll need Pinecone index. You can register or login using this [link](https://app.pinecone.io/?sessionType=signup).

### Step 1

Set the Pinecone API key as an environment variable under the Dependencies section of the workspace

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/pinecone-api-key-env.png" width="800px" alt="pinecone-api-key-env">

### Step 2

Set the Pinecone API key in the `embeddings/job.yaml` file

```yaml
name: calc-embeddings
entrypoint: python embeddings/main.py --mode img --model-name openai  #choose model from [openai, fashionclip], choose mode from [img, txt]
runtime_env:
  working_dir: .
  pip: embeddings/requirements.txt
  env_vars:
    PINECONE_API_KEY: <your pinecone api key> # set your pinecone api key here
```

## 3. Run an Anyscale Job to generate embeddings

### Step 1

Submit the job to generate embeddings by running the following command in your workspace terminal:

```bash
make anyscale-job-embeddings
```

### Step 2

Update the mode and model name in the `embeddings/job.yaml` file to generate embeddings for `img` and `txt` modes and `openai` and `fashionclip` models. For each mode and model combination, submit a new job by running the following command. 

It should be a total of 4 jobs that need to be submitted.

### Step 3

Check the status of each job by visiting the Anyscale Job interface

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/job-status.png" width="800px" alt="job-status">

## 4. Deploy an Anyscale Service to serve the application

### Step 1

Deploy the application by running the following command

```bash
make deploy-app
```

### Step 2

Check the status of the deployment by visiting the

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/service-interface.png" width="800px" alt="service-deployment">

### Step 3

Visit the Application URL to see the application. You can find the URL under the service "Query" dropdown.

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/service-query-dropdown.png" width="800px" alt="service-url">

### Step 4

Query the application by entering a query in the search bar and clicking the search button

<img src="https://anyscale-materials.s3.us-west-2.amazonaws.com/multi-modal-search-deepsense-anyscale/app-query.png" width="800px" alt="app-query">

---

Created with ♥️ by [Anyscale](https://anyscale.com/) and [deepsense.ai](https://deepsense.ai/)
