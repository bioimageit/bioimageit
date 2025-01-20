import os
import argparse
import requests
import getpass
from pathlib import Path
from tqdm import tqdm

# Function to upload a file to GitLab package registry
def upload_package(server_name, package_name, package_version, project_id, file_path, personal_access_token):
    url = f"https://{server_name}/api/v4/projects/{project_id}/packages/generic/{package_name}/{package_version}/{file_path.name}"
    headers = {"PRIVATE-TOKEN": personal_access_token}

    try:
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as file:
            # response = requests.put(url, headers=headers, data=file)

            with tqdm(total=file_size, unit="B", unit_scale=True, desc="Uploading", ncols=80) as progress_bar:
                def progress_callback(monitor):
                    progress_bar.update(monitor.bytes_read - progress_bar.n)

                from requests_toolbelt.multipart.encoder import MultipartEncoderMonitor

                monitor = MultipartEncoderMonitor.from_fields(
                    fields={'file': (file_path.split('/')[-1], file)},
                    callback=progress_callback
                )
                headers['Content-Type'] = monitor.content_type
                response = requests.put(url, headers=headers, data=monitor)

        if response.status_code == 201:
            print("File uploaded successfully!")
        else:
            print(f"Failed to upload file. Status code: {response.status_code}, Response: {response.text}")
    except FileNotFoundError:
        print("Error: The specified file was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Main function to parse arguments and call the upload function
def main():
    parser = argparse.ArgumentParser(
        description="Upload a file to the GitLab package registry.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-f", "--file_path", help="Path to the file you want to upload", type=Path)
    parser.add_argument("-s", "--server", help="Name of the Gitlab server", default="gitlab.inria.fr")
    parser.add_argument("-pn", "--package_name", help="Name of your package", default="1")
    parser.add_argument("-pv", "--package_version", help="Version of your package", default="v1.0")
    parser.add_argument("-pid", "--project_id", help="Your project ID or URL-encoded path (474 for BioImageIT on gitlab-int.inria.fr)", default="54065")

    args = parser.parse_args()

    personal_access_token = getpass.getpass(prompt="Enter your GitLab personal access token: ")

    upload_package(args.server, args.package_name, args.package_version, args.project_id, args.file_path, personal_access_token)

if __name__ == "__main__":
    main()
