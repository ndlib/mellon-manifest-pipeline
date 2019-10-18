echo "[Pre-Build phase] `date` in `pwd`"

echo "Copy the manifest-pipeline.yml to this project so it can run"
echo "$BLUEPRINTS_DIR/deploy/cloudformation/manifest-pipeline.yml"
cp $BLUEPRINTS_DIR/deploy/cloudformation/manifest-pipeline.yml ./

python -m unittest discover  ||  { echo 'Auto Tests Failed' ; exit 1; }
