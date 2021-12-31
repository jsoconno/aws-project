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

def get_terraform_module_dependencies(path, pattern=r"(module[\s]*\"(.*)\"[\s]*{[\s]*.*?\n.*source[\s]*=[\s]*\"(.*)/(.*)/(.*)\?ref=(.*)\")[\s]*#?[\s]*[\s]*(Ignore)?"):
    with open(path) as f:
        path = Path(path)
        contents = f.read()
        results = re.findall(pattern, contents)
        dependencies = []

        for result in results:
            dependency = {
                "file_path": path,
                "filename": path.name,
                "module_ref": result[0],
                "module": result[1],
                "domain": result[2],
                "user": result[3],
                "repo": result[4],
                "ref": result[5],
                "flag": result[6]
            }
            dependencies.append(dependency)
    
    return dependencies

def get_tags(user, repo, token, field=None, regex_pattern=None, group_number=0):
    """
    Get tags from GitHub repo.
    """
    headers = {'Authorization': 'token ' + token}

    response = requests.get(f"https://api.github.com/repos/{user}/{repo}/tags", headers=headers)
    tag_data = json.loads(response.text)

    tag_list = [x["name"] for x in tag_data]

    return tag_list

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

def update_git_tag_ref(file_path, module_ref, current_tag, latest_tag):
    # Read in the file
    with open(file_path, 'r') as f:
        data = f.read()

    # Replace the target string
    new_module_ref = module_ref.replace(current_tag, latest_tag)
    data = data.replace(module_ref, new_module_ref)

    # Write the file out again
    with open(file_path, 'w') as f:
        f.write(data)

def get_next_tag(current_tag, latest_tag, repo_tag_list, allow_major_updates, allow_minor_updates, allow_patch_updates):
    major_version_same = current_tag["major"] == latest_tag["major"]
    minor_version_same = current_tag["minor"] == latest_tag["minor"]
    patch_version_same = current_tag["patch"] == latest_tag["patch"]

    current_tag_components = get_semantic_version_components(current_tag["git_tag"])
    latest_tag_components = get_semantic_version_components(latest_tag["git_tag"])

    if current_tag == latest_tag:
        latest_allowed_tag = latest_tag["git_tag"]
    elif current_tag["major"] == latest_tag["major"] and current_tag["minor"] == latest_tag["minor"] and current_tag["patch"] < latest_tag["patch"] and allow_patch_updates:
        latest_allowed_tag = latest_tag["git_tag"]
    elif current_tag["major"] == latest_tag["major"] and current_tag["minor"] < latest_tag["minor"] and allow_minor_updates:
        latest_allowed_tag = latest_tag["git_tag"]
    elif current_tag["major"] == latest_tag["major"] and current_tag["minor"] < latest_tag["minor"] and allow_patch_updates:
        allowed_tags = []
        for git_tag in repo_tag_list:
            # print(git_tag)
            regex_pattern = f'({current_tag_components["major"]}\.{current_tag_components["minor"]}\.\d*)'
            result = re.findall(regex_pattern, git_tag)
            if result:
                allowed_tags.append(result[0])
        if allowed_tags:
            latest_allowed_tag = allowed_tags[0]
        else:
            latest_allowed_tag = None
    elif current_tag["major"] < latest_tag["major"] and allow_major_updates:
        latest_allowed_tag = latest_tag["git_tag"]
    elif current_tag["major"] < latest_tag["major"] and allow_minor_updates:
        allowed_tags = []
        for git_tag in repo_tag_list:
            regex_pattern = f'({current_tag_components["major"]}\.\d*\.\d*)'
            result = re.findall(regex_pattern, git_tag)
            if result:
                allowed_tags.append(result[0])
        if allowed_tags:
            latest_allowed_tag = allowed_tags[0]
    elif current_tag["major"] < latest_tag["major"] and allow_patch_updates:
        allowed_tags = []
        for git_tag in repo_tag_list:
            regex_pattern = f'({current_tag_components["major"]}\.{current_tag_components["minor"]}\.\d*)'
            result = re.findall(regex_pattern, git_tag)
            if result:
                allowed_tags.append(result[0])
        if allowed_tags:
            latest_allowed_tag = allowed_tags[0]
        else:
            latest_allowed_tag = None
    elif current_tag["git_tag"] in repo_tag_list:
        latest_allowed_tag = current_tag["git_tag"]
    else:
        latest_allowed_tag = latest_tag["git_tag"]

    return latest_allowed_tag

token = os.environ["PAT_TOKEN"]

# Make these pipeline configuration items
allow_major_updates = False
allow_minor_updates = True
allow_patch_updates = True

terraform_folder_path = Path(__file__).parent
terraform_files = [str(x) for x in terraform_folder_path.glob('*.tf') if x.is_file()]

for f in terraform_files:
    dependencies = get_terraform_module_dependencies(f)

    for dependency in dependencies:
        file_path=dependency["file_path"]
        filename = dependency["filename"]
        module_ref=dependency["module_ref"]
        module = dependency["module"]
        user = dependency["user"]
        repo = dependency["repo"]
        flag = dependency["flag"]
        current_tag = get_semantic_version_components(dependency["ref"])
        repo_tag_list = get_tags(user, repo, token=token, field="name")
        latest_tag = get_semantic_version_components(repo_tag_list[0])

        latest_allowed_tag = get_next_tag(current_tag, latest_tag, repo_tag_list, allow_major_updates, allow_minor_updates, allow_patch_updates)

        if latest_allowed_tag == current_tag["git_tag"]:
            print(f'{bcolors.OKGREEN}The module {module} in file {filename} is using the latest version ({current_tag["git_tag"]}).{bcolors.ENDC}')
        else:
            print(f'{bcolors.FAIL}The module {module} in file {filename} is not using the latest allowed version (Bumping from {current_tag["git_tag"]} -> {latest_allowed_tag}).{bcolors.ENDC}')
            update_git_tag_ref(file_path, module_ref, current_tag["git_tag"], latest_allowed_tag)