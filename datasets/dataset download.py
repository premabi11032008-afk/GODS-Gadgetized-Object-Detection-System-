import kagglehub

# Download latest version
path = kagglehub.dataset_download("programmerrdai/road-issues-detection-dataset")

print("Path to dataset files:", path)