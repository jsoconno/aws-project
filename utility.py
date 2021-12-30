from pathlib import Path
import re
import requests
import json
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_terraform_module_dependencies(path, pattern=r"module[^\S\n\t]+?\"(.*)\"[^\S\n\t]{.*?\n.*source[^\S\n\t]+?=[^\S\n\t]+?\"(.*)/(.*)/(.*)\?ref=(.*)\""):
    with open(path) as f:
        path = Path(path)
        contents = f.read()
        result = re.findall(pattern, contents)
        dependencies = []

        for result in result:
            dependency = {
                "file_path": path,
                "filename": path.name,
                "module": result[0],
                "domain": result[1],
                "user": result[2],
                "repo": result[3],
                "ref": result[4]
            }
            dependencies.append(dependency)
    
    return dependencies

def get_latest_tag(user, repo, token, field=None, regex_pattern=None, group_number=0):
    """
    Get tags from GitHub repo.
    """
    headers = {'Authorization': 'token ' + token}

    response = requests.get(f"https://api.github.com/repos/{user}/{repo}/tags", headers=headers)
    latest_tags_data_dict = json.loads(response.text)[0]

    if field:
        field_value = latest_tags_data_dict[field]
        if regex_pattern is None:
            output = field_value
        else:
            output = re.search(regex_pattern, field_value).group(group_number)
    else:
        output = latest_tags_data_dict

    return output

def get_semantic_version_components(git_tag):
    regex_pattern = r"(\d*)\.(\d*)\.(\d*)[^a-zA-Z\d\s:]?(.*)"
    result = re.search(regex_pattern, git_tag)

    components = {
        "git_tag": result[0],
        "major": result[1],
        "minor": result[2],
        "patch": result[3],
        "pre_release": result[4]
    }

    return components

token = os.environ["PAT_TOKEN"]

terraform_folder_path = Path(__file__).parent
terraform_files = [str(x) for x in terraform_folder_path.glob('*.tf') if x.is_file()]

for f in terraform_files:
    dependencies = get_terraform_module_dependencies(f)

    for dependency in dependencies:
        filename = dependency["filename"]
        module = dependency["module"]
        user = dependency["user"]
        repo = dependency["repo"]
        current_tag = get_semantic_version_components(dependency["ref"])
        latest_tag = get_semantic_version_components(get_latest_tag(user, repo, token=token, field="name"))

        if current_tag == latest_tag:
            print(f'{bcolors.OKGREEN}The module {module} in {filename} with version {current_tag["git_tag"]} is up-to-date.{bcolors.ENDC}')
        else:
            if current_tag["major"] != latest_tag["major"]:
                print(f'{bcolors.WARNING}MAJOR: The {module} in {filename} is behind by a major version.  {current_tag["git_tag"]} -> {latest_tag["git_tag"]} (latest).{bcolors.ENDC}')
            elif current_tag["minor"] != latest_tag["minor"]:
                print(f'{bcolors.FAIL}MINOR: The module {module} in {filename} is behind by a minor version.  {current_tag["git_tag"]} -> {latest_tag["git_tag"]} (latest).{bcolors.ENDC}')
            elif current_tag["patch"] != latest_tag["patch"]:
                print(f'{bcolors.FAIL}PATCH: The module {module} in {filename} is behind by a patch version.  {current_tag["git_tag"]} -> {latest_tag["git_tag"]} (latest).{bcolors.ENDC}')
            elif current_tag["pre_release"] != latest_tag["pre_release"]:
                print(f'{bcolors.OKGREEN}PRE-RELEASE: There is a pre-release available for module {module} in {filename}.  Consider experimenting with {latest_tag["git_tag"]}.{bcolors.ENDC}')
            else:
                print("Something went wrong.")