#!/bin/bash

# Check if at least one argument is provided
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <root_directory> [<ignore_dir1> <ignore_dir2> ...]"
  exit 1
fi

# Normalize paths by converting backslashes to forward slashes
normalize_path() {
  echo "$1" | sed 's|\\|/|g'
}

# First argument is the root directory (normalized)
root_directory=$(normalize_path "$1")
shift

ignore_dirs=("$@")

# Change to the root directory
cd "$root_directory" || { echo "Failed to change directory to $root_directory"; exit 1; }

# Initialize the find command components
find_cmd=(find .)

# Build the ignore expression if there are any ignore directories
if [ "${#ignore_dirs[@]}" -gt 0 ]; then
  find_cmd+=( \( )
  for idx in "${!ignore_dirs[@]}"; do
    ignore_dir="${ignore_dirs[$idx]}"
    normalized_ignore_dir=$(normalize_path "$ignore_dir")
    find_cmd+=( -path "./$normalized_ignore_dir" -prune )
    if [ $((idx + 1)) -lt ${#ignore_dirs[@]} ]; then
      find_cmd+=( -o )
    fi
  done
  find_cmd+=( \) -o )
fi

# Add the rest of the find command
find_cmd+=( -type f \( -name "*.tsx" -o -name "*.json" -o -name "*.ts*" -o -name "*.py" -o -name "*.local" -o -name "*.js" -o -name "*.py" -o -name "*.css" \) -print )

# Initialize or clear the output file
> output.txt

# Execute the find command and process the files
"${find_cmd[@]}" | while IFS= read -r file; do
  echo "### $root_directory/$file:" >> output.txt
  echo -e "\n" >> output.txt

  # Read the file content
  file_content=$(cat "$file")

  # Get the explanation from GPT (Commented out as per your original script)
  # explanation=$(get_explanation "$file_content")
  # echo -e "\n" >> output.txt
  # Append the explanation to the output file
  # echo "$explanation" >> output.txt
  # echo -e "\n" >> output.txt

  # Add triple backticks before the file content
  echo '```' >> output.txt

  # Append the file content
  cat "$file" >> output.txt

  echo -e "\n" >> output.txt
  # Add triple backticks after the file content
  echo '```' >> output.txt

  # Add spacing between entries
  echo -e "\n\n" >> output.txt
done
