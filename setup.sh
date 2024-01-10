#!/bin/bash

function install_dependencies() {
    sudo apt-get update &&
        sudo apt-get install -y --no-install-recommends \
            locales &&
        sudo locale-gen "en_US.UTF-8"

    sudo update-locale "LANG=en_US.UTF-8" &&
        sudo locale-gen --purge "en_US.UTF-8" &&
        sudo dpkg-reconfigure --frontend noninteractive locales

    sudo apt-get update &&
        sudo apt-get -y --no-install-recommends install \
            bash-completion bash \
            libffi-dev \
            build-essential libssl-dev zlib1g-dev \
            libbz2-dev libreadline-dev libsqlite3-dev curl &&
        sudo apt-get -y clean &&
        sudo apt-get -y autoremove
}

function install_pyenv() {
    if [ ! -e ~/.pyenv ]; then
        curl https://pyenv.run | bash
    fi
}

function update_requirements() {
    pyenv install --skip-existing "3.9.18" "3.8.18" "2.7.18" "3.12.1"
    pyenv local "3.9.18" "3.8.18" "2.7.18" "3.12.1"

    rm -rf ./.venv
    PYENV_VERSION="3.8.18" pyenv exec python -m pip install --upgrade pip
    PYENV_VERSION="3.8.18" pyenv exec python -m pip install --user pip-tools validate-pyproject\[all\] tomli
    PYENV_VERSION="3.8.18" pyenv exec python -m piptools compile \
        --constraint requirements/constraints.txt \
        --build-isolation \
        --verbose \
        --strip-extras \
        --newline LF \
        --no-allow-unsafe \
        --no-reuse-hashes \
        --no-emit-trusted-host \
        --no-emit-options \
        --no-emit-find-links \
        "$@" \
        ./pyproject.toml
}
function main() {
    set -eax

    if [ ! "${1:-}" = "--skip" ]; then
        install_dependencies
        install_pyenv
    fi

    update_requirements --all-extras -o requirements.txt

    echo "Finished initial setup of 'oschmod' project."
}

main "$@"
