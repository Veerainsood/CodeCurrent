docker run -dit --name cpp_parser_container \
  --mount type=bind,src="$(pwd)",dst=/src \
  veerain/cplusplusparser:latest bash
