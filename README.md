# NightCrawler Datascience Pipeline Repository

This repo provides the NightCrawler pipeline as well as a CLI to run it.

## Setting the CLI up in your local environment

1. Pull the latest changes from the git repository.

```bash
git pull
```

2. Install postgresql development library

2.1 On debian based linux:

```sh
sudo apt-get install -y libpq-dev build-essential
```

2.2 On Mac OS:

```sh
brew install libpq
export LDFLAGS="-L/opt/homebrew/opt/libpq/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libpq/include"
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
```

3. Create a virtual environment with Poetry and activate it.

```bash
poetry shell
```

> **_NOTE:_**  Run the following command to install Poetry if it was not installed:
>```sh
>curl -sSL https://install.python-poetry.org | python3 -
>```

4. Install the project dependencies.

```bash
poetry install --directory ./pyproject.toml
```

5. Copy `.env_template` to `.env`. Fill with your credentials and source it by running `source .env`.

## CLI overview
As of today, the CLI looks as follows:

![nc_pipeline](https://github.com/user-attachments/assets/3ca8b11b-a688-4449-abd3-29d6781917c4)



## Basic CLI usage
First, activate the venv inside the `nightcrawler` directory:

```bash
poetry shell
```

Then from the root directory you can use the `nightcrawler cli` as follows:
```
python -m nightcrawler <processing_step> <param_1> <param_n> 

```

You can always use the `-h` to see all available options for the cli.


### Processing steps
The pipeline contains 9 processing steps:

| Step   | Name        | Inherits from and implemented in | Description                      |
|--------|-------------|----------------------------------|----------------------------------|
| **1** | Extract URLs using Serpapi | [BaseStep>Extract>SerpapiExtractor](./nightcrawler/extract/s01_serp_api.py)| Extract URLs using Serpapi based on a keyword provided by the users |
| **2** | Enrich keywords | [BaseStep>GoogleLenseApi](./nightcrawler/extract/s02_enriched_keywords.py) | (EXERIMENTAL) collect for each keyword additional results by adding related terms i.e. buying to the query. |
| **3** | Google Lens Search | [BaseStep>Extract>GoogleLenseApi](./nightcrawler/extract/s03_google_lens.py) | Use serpapi to perform a Google Lens search. |
| **4** | Structure data with Zyte | [BaseStep>Extract>ZyteExtractor](./nightcrawler/extract/s02_zyte.py)| Use Zyte to retrieve structured information from each URL collected by serpapi |
| **5** | Processing | [BaseStep>DataProcessor](./nightcrawler/process/s03_dataprocessor.py) | Apply some (for the time-being) manual filtering logic: filter based on URL, currency and blacklists. All these depend on the --unit input of the pipeline call.  |
| **6** | Delivery policy filtering |  [BaseStep](./nightcrawler/process/s04_filter_swiss_result.py) | delivery policy filtering based on offline analysis of domains public delivery information |
| **7** | Page type detection |  [BaseStep>DeliveryPolicyDetector](./nightcrawler/process/s05_delivery_page_detection.py)  | The pipeline uses by default a probability calculated by Zyte indicating, if the page is an ecommerce page or not. You can change this to using a custom BERT modell served on the GPU by setting the argument '--page-type-detection-method=infer'. |
| **8** | Webpage Blocker Detection |  [BaseStep>PageTypeDetector](./nightcrawler/process/s06_page_type_detection.py) | Blocked / corrupted content detection based the prediction with a BERT model. If the content is blocked, the results should be shown to the user, therefore, they bypass the remaining pipeline steps. |
| **9** | Product Type Relevence per Organization |  [BaseStep>BlockedContentDetector](./nightcrawler/process/s07_blocket_content_detection.py) | Classification if the product type is relvant to the target organization domain (i.e. pharmaceutical for Swissmedic AM or medical device for Swissmedic MD) |
| **10** | Relevance Classifier |  [BaseStep>ContentDomainDetectors](./nightcrawler/process/s08_content_domain_detection.py) | Binary classifier per organisation, whether a product is classified as suspicious or not. |
| **11** | Ranking and Filtering |  [BaseStep>ResultRanker](./nightcrawler/process/s10_result_ranker.py) | Apply any kinf of (rule-based?) ranking or filtering of results. If this last step is really needed needs be be confirmed, maybe this step will fall away|

> **_NOTE:_**  For a simple start, I suggest to start from the [full pipeline CLI](./nightcrawler/cli/full_pipeline.py) file.


### Full Pipeline Run
To perform a full end-to-end pipeline run (this is what will ultimately be deployed via Azure Functions):

```bash
python -m nightcrawler fullrun viagra -n=3
```

To run the pipeline and filter only for a given unit run:
```bash
python -m nightcrawler fullrun viagra -n=3 --unit="Swissmedic AM"
```

See all CLI options in the below table:

| Options                                                | Level             | For                             | Description                                                                                                      |
|-------------------------------------------------------|-------------------|---------------------------------|------------------------------------------------------------------------------------------------------------------|
| `-h, --help`                                           | Global            | All commands                    | Show the help message and exit                                                                                   |
| `--log-level LOG_LEVEL`                                | Global            | All commands                    | Set the log level (default: INFO)                                                                                |
| `--log-file LOG_FILE`                                  | Global            | All commands                    | Log to file (default: None)                                                                                      |
| `-v, --version`                                        | Global            | All commands                    | Show the program's version number and exit                                                                       |
| `{extract, process, fullrun}`                          | Positional        | All commands                    | Modules available: extract (calls extractor class), process (calls processor class), and fullrun (full pipeline) |
| `extract`                                              | Positional        | All commands                    | Calls the extractor class                                                                                       |
| `process`                                              | Positional        | All commands                    | Calls the processor class                                                                                       |
| `fullrun`                                              | Positional        | All commands                    | Runs the full pipeline from extraction to processing                                                            |
| `searchitem`                                              | Positional        | `fullrun`                       | Keyword or URL (with `-r` parameter) to search for                                                                                           |
| `-n NUMBER_OF_RESULTS, --number-of-results NUMBER_OF_RESULTS` | Option    | `fullrun`                       | Set the maximum number of results from Serpapi (default: 0 -> return all., max: 3 per Google Shopping, Google Site Search, Google, and eBay) |
| `--country {CH,AT,CL}`                                 | Option            | `fullrun`                       | Processes URLs using a country-specific pipeline                                                                |
| `--org ORG`                                 | Option            | `fullrun`                       | Processes URLs using an organization-specific pipeline                                                                |
| `-r GOOGLE_LENS_SEARCH [GOOGLE_LENS_SEARCH ...], --google-lens-search GOOGLE_LENS_SEARCH [GOOGLE_LENS_SEARCH ...]` | Option | `fullrun` | List of image URLs for google lens search                                                                      |
| `--case-id CASE_ID`                                 | Option            | `fullrun`                       | Database case identifier (only usefull for db storage)                                                                |
| `--keyword-id KEYWORD_ID`                                 | Option            | `fullrun`                       | Database keyword identifier (only usefull for db storage)                                                                |

### Extraction
To run the full extraction pipeline you can use any of the following commands:
```bash
python -m nightcrawler extract aspirin #full extraction with keyword 'aspirin'
python -m nightcrawler extract aspirin -n=3 #full extraction with keyword 'aspirin' for the first 3 entries per serpapi (3 per google shopping, google site search, google and ebay = 12 URLs total)
python -m nightcrawler fullrun -r -n=10 https://www.qualipet.ch/cache/f3a1a59a49af25df/d18f52c8ec6a4c4b/6020504K_1%28r800x800%29.jpg\?d\=20240610161345 --unit="Swissmedic AM" #full extraction with google lens search


```
Running the extraction pipeline will log the results in the terminal (with default logging which is `--log-level INFO`) and store the scraped content into `./data/output/<extraction_step>_<timespamp>_<user>.json`.


If you prefer, you can run the pipeline for a single extraction step:
1. Collect only the URLs from serpapi: 
```bash
python -m nightcrawler extract triofan -n=3 --step=serpapi  #collect only the 3 first URLs from serpapi for the keyword triofan  (3 per google shopping, google site search, google and ebay = 12 URLs total)
```

2. Collect only the parsed results from zyte (line 2 below):

```bash
python -m nightcrawler extract triofan -n=3 --step=zyte --urlpath=<url_path>-- #collect the parsed results for keyword triofan from zyte. the url path should reference to the results of the previous step, typically in ./data/output/<timestamp>_<keyword>_<user>/01_extract_serpapi.json
```
### Processing
Process all files within a given results directory:
```bash
python -m nightcrawler process 20240823_210829_triofan_defaultuser
```

Process files only for a given unit:
```bash
python -m nightcrawler process --unit="Swissmedic AM" 20240823_210829_triofan_defaultuser
```



## Development settings
### Configuration
The  [**settings**](nightcrawler/settings.py) component is designed to store all variables that are not tied to specific commands and do not change throughout the runtime of the CLI. On the other hand, [**context**](nightcrawler/context.py) is intended to include variables that originate from the command line, as well as any helpers or long-lived objects (e.g., database connections). While it’s possible to consolidate everything into the settings, having a separate Context object can be beneficial as the codebase expands. This distinction helps maintain organization and scalability as the project grows.

### Database usage

- Run postgres with citus-data extension:

```sh
docker run -id \
    --name nightcrawler \
    -e POSTGRES_PASSWORD=secret \
    -e POSTGRES_USER=user \
    -e POSTGRES_DB=nightcrawler \
    -p 5432:5432 \
    citusdata/citus:12.1
```

- Run azurite (Azure blob service emulator):

```sh
docker run -i -d \
     --name azurite \
     -p 10000:10000 -p 10001:10001 -p 10002:10002 \
     mcr.microsoft.com/azure-storage/azurite
```

- Configure 3 containers:

```sh
for blob in images processing public;do docker run -it --rm --network host mcr.microsoft.com/azure-cli az storage container create -n ${blob} --connection-string "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;";done;
```

- Run migration:

```sh
python ./venv/lib/python3.10/site-packages/libnightcrawler/cli cases list
```

- Insert case and keyword:

```sh
docker exec -it nightcrawler psql -U user nightcrawler -c "insert into cases (org_id, id, name, notifications_enabled, inactive) values (1, 4567, 'test', false, false);insert into keywords(id, case_id, notifications_enabled, query, type, crawl_state) values (111, 4567, false, 'aspirin', 'TEXT', 'PENDING');"
```

- Enable db usage:

```sh
export NIGHTCRAWLER_USE_FILE_STORAGE=false
```

- Add arguments `--case-id` and `keyword-id` to the `fullrun` command:

```sh
python nightcrawler fullrun aspirin -n 1 --org="Swissmedic MEP" --case-id 4567 --keyword-id 111
```

### Logging
The default logging level is set to `INFO`, and by default, logs are not stored in a file but are output to the console. 
If you want to change the default behavior, you can use the following command-line options:

- **Change the log level**: Use the `--log-level` option to set the desired log level. Available levels include `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. For example:
  ```bash
  python -m nightcrawler extract serpapi aspirin --log-level DEBUG
  ```
- **Log to a file**: Use the --log-file option to specify a file where the logs should be stored. For example:
  ```bash
  python -m nightcrawler extract serpapi aspirin --log-file logs/output.log
  ```


> **_NOTE:_**  For simplicity, the full CLI documentation can be found on [Confluence](https://swissmedic.atlassian.net/wiki/spaces/N/pages/7475365463/CLI).



### Linting and Formatting
Based on Thomas recommendation we will be using [ruff](https://docs.astral.sh/ruff/) as linting and formatting tool.
For linting preview run:
```bash
ruff check
```
For linting run:
```bash
ruff check --fix
```

Ruff also provides a formatting tool that should be run prior commiting changes:
```bash
ruff format
``` 

## Testing
Currently two kind of tests are implemented, both using the pytest package:

### Smoke tests
Smoke tests are used to test the pipeline end-to-end. For the CLI, we want to run the full pipeline with the keyword ‘aspirin’. The smoke tests mimic the following command:

``` bash
python -m nightcrawler fullrun aspirin -n=1
``` 

After running the entire pipeline, the test checks for the following conditions:
1. The logs contain some specific information on successfull execution.
2. The output directory contains the 4 output files.

The tests are found in `./tests/smoke` and can be run as follows:

``` bash
pytest --cov=nightcrawler tests/smoke -s
``` 

> **_NOTE:_**  The `-s` flag is used to print the stdout along the pytest logs. It is not needed but in case of a failing test it provides you with the stdout for debuging reasons.

### Unit tests
The unit tests are more granular im comparison with the smoke test and test the standalone function of each component. To run all unit tests you can run:

``` bash
pytest --cov=nightcrawler --cov-report=html tests/unit -s
``` 
> **_NOTE:_**  The `--cov-report` flag is optional and will provide an htmlcov holder in the root-directory.

## Git Tag History
So far, no tags have been created (alho, 12.08.2024).
