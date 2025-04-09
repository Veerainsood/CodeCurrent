#!/bin/bash
docker run -dit --name cplusplusparser --mount type=bind,source="$(pwd)",target=/src veerain/cplusplusparser:latest bash
