#!/bin/bash
echo "[Install phase] `date` in `pwd`"

# install dependencies for specific lambdas
pushd process_manifest
./local_install.sh
popd

pushd init
./local_install.sh
popd

pushd finalize
./local_install.sh
popd

pushd museum_export
./local_install.sh
popd

pushd aleph_export
./local_install.sh
popd

pushd curate_export
./local_install.sh
popd

pushd archivesspace_export
./local_install.sh
popd

pushd bendo_export
./local_install.sh
popd

pushd metadata_rules
./local_install.sh
popd

pushd object_files_api
./local_install.sh
popd

pushd collections_api
./local_install.sh
popd
