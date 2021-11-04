export UI_PATH=server/frontend/
npm run --prefix $UI_PATH build
cp -r ${UI_PATH}build server/frontend/
