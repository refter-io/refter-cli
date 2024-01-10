from os import environ

CONFIG_KEY = "refter"
API_HOST = "https://refter.io/api"
API_ENDPOINT = "deployment"

CI = environ.get("CI", "false") == "true"
CI_BRANCH = environ.get("CI_BRANCH")
CI_COMMIT = environ.get("CI_COMMIT")
