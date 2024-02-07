## This file is sourced by ./bin/configure-local

ci_file=debian/kali-ci.yml

if [ -e "${ci_file}.disabled" ] \
&& [ ${opt_verbose} -gt 1 ]; then
  echo "Found disabled CI file: $( pwd )/${ci_file}.disabled"
elif [ ! -e "${ci_file}.disabled" ]; then
  create_if_missing "${ci_file}" <<END
include:
  - https://gitlab.com/kalilinux/tools/kali-ci-pipeline/raw/master/recipes/kali.yml
END
  record_change "Add GitLab's CI configuration file" "${ci_file}"

  if grep -q    "gitlab-ci/kali/templates.yml" "${ci_file}"; then
    sed -i -e "s|gitlab-ci/kali/templates.yml|recipes/kali.yml|" \
           -e "/pipeline-jobs.yml/d" \
           "${ci_file}"
    record_change "Update URL in GitLab's CI configuration file" "${ci_file}"
  fi
fi
