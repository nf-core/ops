# Pulumi

[Pulumi Shell Plugin](https://developer.1password.com/docs/cli/shell-plugins/pulumi/)

[How to use 1Password with different accounts automatically](https://developer.1password.com/docs/cli/shell-plugins/multiple-accounts/)

```console
cd ~/src/nf-core

op signin

# Select nf-core

op plugin init pulumi
```

This should result in:
```

Pulumi CLI
Authenticate with Pulumi Personal Access Token.

? Locate your Pulumi Personal Access Token: Search in 1Password...

? Locate your Pulumi Personal Access Token: Pulumi Personal Access Token (Private)

? Configure when the chosen credential(s) will be used to authenticate: Use automatically when in this directory or subdirectories
```
