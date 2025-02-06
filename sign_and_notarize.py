import argparse
import os
import urllib
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
parser.add_argument("--target-os",
                    help=f'The OS signature should be made for',
                    default='MacOS')
parser.add_argument("--file-to-sign",
                    help=f'The name of the file to sign', required=False)
parser.add_argument("--output-name",
                    help=f'The name of the file to store in output-dir', required=False)
parser.add_argument('--verbose', help="Run commands with verbose output requested", action="store_true")
parser.add_argument('--skip-upload', help="Do not repeat upload step", action="store_true")
args = parser.parse_args()

client = SignServerClient(
    software_name=args.soft_name,
    version_name=args.version_name,
    ci_job_token=args.ci_job_token,
    verbose=args.verbose,
    target_os=args.target_os
)


def final_file(path):
    if args.output_name:
        return f'{args.output_dir}/{args.output_name}'
    else:
        return f'{args.output_dir}/signed_{os.path.basename(urllib.parse.urlsplit(path).path)}'


def should_package_as_dmg():
    return 'PACKAGE_AS_DMG' in os.environ and os.environ['PACKAGE_AS_DMG'] == "1"


def notarize(notarized_path):
    submission_id = client.notarize(notarized_path, '')
    submission_info = client.wait_for_notarization_end(submission_id, wait_interval=20)
    final_status = submission_info["status"]
    if final_status == 'Invalid':
        log = client.get_notarization_log(submission_id)
        print(log)
        raise SystemExit(f'Notarization failed: final status is Invalid')
    return final_status == 'Accepted'


def mac_os_sign():
    if not args.skip_upload:
        # upload files to the server
        for file_to_upload in ['entitlements.plist', os.environ['UNSIGNED_TARFILE']]:
            client.upload(file_to_upload)
    
    client.sign([f'{client.software}.app/Contents/Frameworks/lib-dynload/*'], f'--options=runtime --force --verbose 2')
    client.sign([f'{client.software}.app/Contents/Frameworks/charset_normalizer/*'], f'--options=runtime --force --verbose 2')
    client.sign([f'{client.software}.app/Contents/Frameworks/psutil/*'], f'--options=runtime --force --verbose 2')
    client.sign([f'{client.software}.app/Contents/Frameworks/yaml/*'], f'--options=runtime --force --verbose 2')
    client.sign([f'{client.software}.app/Contents/Frameworks/*'], f'--options=runtime --force --verbose 2')
    client.sign([f'{client.software}.app/Contents/MacOS/bioimageit'], f'--options=runtime --entitlements entitlements.plist --force --verbose 2')
    client.sign([f'{client.software}.app'], f'--options=runtime --entitlements entitlements.plist --force --verbose 2')

    client.pretty_print_inspected_path(client.inspect_path(client.software + '.app'))

    if should_package_as_dmg():
        unsigned_dmg = client.makedmg(format='UDBZ', fs='hfs+')
        client.sign([unsigned_dmg], '--verbose=2')
        notarized_path = unsigned_dmg
    else:
        notarized_path = client.software + '.app'

    if not notarize(notarized_path):
        print('Notarization failed !')
        return

    path = client.staple(notarized_path, '')
    if not should_package_as_dmg():
        path = client.package(notarized_path, '')
    client.download(path_with_params=path, output_file=final_file(path))



def windows_sign():
    if not args.file_to_sign:
        file_to_sign = client.software + '.exe'
    else:
        file_to_sign = args.file_to_sign
    if not args.skip_upload:
        result = client.upload(file_to_sign)
    verbosity = ''
    if args.verbose:
        verbosity = '--verbose'
    result = client.sign([file_to_sign], verbosity)
    if args.verbose:
        print(result)
    client.download(path_with_params=result['url'], output_file=final_file(result["url"]))


if args.target_os == 'Win':
    windows_sign()
else:
    mac_os_sign()
