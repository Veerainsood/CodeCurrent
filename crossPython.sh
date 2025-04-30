# final_file="./caller_callee_pairs_final.json"
# rm -f "$final_file"
# echo "[" > "$final_file"
# first=1

# Loop over each Java source file
while IFS= read -r f; do
  echo "Parsing: $f"

  # Run the Java AST generator (produces output.json)
  python3 python_cross_final.py "$f" || continue
  # Run the enrichment step (produces caller_callee_pairs.json)
  # python3 /ast/parse2Jsons_java.py /ast/output.json parser_output.json || continue

  # Extract entries and merge
#   entries=$(jq -c '.[]' /ast/caller_callee_pairs.json 2>/dev/null)

#   if [ -n "$entries" ]; then
#     if [ $first -eq 1 ]; then
#       echo "$entries" | paste -sd "," - >> "$final_file"
#       first=0
#     else
#       echo "," >> "$final_file"
#       echo "$entries" | paste -sd "," - >> "$final_file"
#     fi
#   fi
done < <(find . -type f -name "*.py")

# # Finalize the JSON array
# echo "]" >> "$final_file"

# # Copy to /src for use elsewhere
# cp /ast/caller_callee_pairs_final.json /src/function_calls_java.json