install:
    npm install
    npx husky init
    echo "npx commitlint --edit \$1 --config ./.linters/config/commitlint.config.js" > .husky/commit-msg
    echo "just lint" > .husky/pre-commit

lint:
    docker run -v $(pwd):/app -v $(pwd)/.linters:/polylint/.linters outoforbitdev/polylint:0.1.0
