#!/bin/sh

cd `dirname $0`/..

# Prepare target directory
rm -rf dist
mkdir -p dist/postsai
mkdir dist/postsai/resources

# Copy resources
cp -ax *.md *.py *.txt resources                  dist/postsai

# Angular build
cd frontend
rm -rf dist
ng build
cd ..

# Move and post-process angular build
mv frontend/dist/frontend/* dist/postsai/resources/
rm -rf dist/postsai/resources/assets/fonts

sed 's|src="|src="resources/|g' < dist/postsai/resources/index.html | sed 's|href="|href="resources/|g' | sed 's|url(|url(resources/|g' | sed 's|<base href="resources//">|<base href=".">|' | sed 's|resources/resources|resources|' > dist/postsai/index.html
cp dist/postsai/index.html dist/postsai/query.html 
cp dist/postsai/index.html dist/postsai/search.html

# Copy backend
cp --parents backend/*.py extensions/__init__.py  dist/postsai
rm dist/postsai/config.py*

# Create .zip file
cd dist
zip -r postsai-$npm_package_version.zip postsai

