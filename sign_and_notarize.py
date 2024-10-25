import argparse
import os
from sign_server.wsgi.client import SignServerClient
 
parser = argparse.ArgumentParser()
parser.add_argument("--version-name",
  help=f'The version_name used to create the output directory on the sign server',
  required=True)
parser.add_argument("--soft-name",
  help=f'Name of the software to be signed, as known to the [qlf-]signedby.inria.fr service acting as authorization server',
  required=True)
parser.add_argument("--ci-job-token",
  help=f'The token to pass to http calls so the server can verify the legimity of calls to its API',
  required=True)
parser.add_argument("--output-dir",
  help=f'This directory downloaded artifacts should be stored in',
  default='artifacts')
parser.add_argument('--verbose', help="Run commands with verbose output requested", action="store_true")
parser.add_argument('--skip-upload', help="Do not repeat upload step", action="store_true")
args=parser.parse_args()
 
client=SignServerClient(
  software_name = args.soft_name,
  version_name = args.version_name,
  ci_job_token = args.ci_job_token,
  verbose = True,
  target_os = 'MacOS'
)
 
if not args.skip_upload:
  # upload files to the server
  for file_to_upload in ['BioImageIT.entitlements', os.environ['UNSIGNED_TARFILE']]:
    result=client.upload(file_to_upload)
 
# client.sign(['BioImageIT_v0.3.9.app/Contents/MacOS/Plugins/*'], '--deep --force --verbose 2')
 
client.sign(['BioImageIT_v0.3.9.app'], f'--options=runtime --entitlements BioImageIT.entitlements --verbose 2')
 
submission_id = client.notarize('BioImageIT_v0.3.9.app', '')
 
submission_info=client.wait_for_notarization_end(submission_id, wait_interval=20)
 
final_status=submission_info["status"]
 
if final_status == 'Invalid':
  log = client.get_notarization_log(submission_id)
  print(log)
  raise SystemExit(f'Notarization failed')
 
if final_status == 'Accepted':
  client.staple('BioImageIT_v0.3.9.app', '')
  path=client.package('BioImageIT_v0.3.9.app', '')
  client.download(path=path, output_file=f'{args.output_dir}/{args.soft_name}-{args.version_name}-signed.tgz')