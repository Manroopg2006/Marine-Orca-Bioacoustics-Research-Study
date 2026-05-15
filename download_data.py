from dagshub.streaming import DagsHubFilesystem

fs = DagsHubFilesystem(".", repo_url="https://dagshub.com/DagsHub-Datasets/orcasound-dataset")

# Fix for Windows - use this instead
files = fs.listdir("/")
print(files)