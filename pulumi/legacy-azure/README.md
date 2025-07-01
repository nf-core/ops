# Legacy Azure Resources

> **Note:** Our Azure credits ran out and it's unclear at this point if we will get any more. Please shout if anyone can think of any infra that relies on Azure so that we can mitigate this.
>
> Slack discussion: https://nfcore.slack.com/archives/C069B2Z5P1R/p1751276871909109

## Azure Resources Inventory

This document contains a record of all Azure resources that were provisioned in our account before the credits ran out.

### Virtual Machines

- **bastion-server** (West Europe, nf-nomad-dev-rg)
- **hashistack-client-0** (West Europe, nf-nomad-dev-rg)
- **hashistack-client-1** (West Europe, nf-nomad-dev-rg)
- **hashistack-client-2** (West Europe, nf-nomad-dev-rg)
- **hashistack-server-0** (West Europe, nf-nomad-dev-rg)
- **hashistack-server-1** (West Europe, nf-nomad-dev-rg)
- **hashistack-server-2** (West Europe, nf-nomad-dev-rg)
- **igenomes-data-sync** (West Europe, igenomes-data-sync_group)

### Disks

- **bastion-server-osdisk** (West Europe, NF-NOMAD-DEV-RG)
- **hashistack-client-osdisk-0** (West Europe, NF-NOMAD-DEV-RG)
- **hashistack-client-osdisk-1** (West Europe, NF-NOMAD-DEV-RG)
- **hashistack-client-osdisk-2** (West Europe, NF-NOMAD-DEV-RG)
- **hashistack-server-osdisk-0** (West Europe, NF-NOMAD-DEV-RG)
- **hashistack-server-osdisk-1** (West Europe, NF-NOMAD-DEV-RG)
- **hashistack-server-osdisk-2** (West Europe, NF-NOMAD-DEV-RG)
- **igenomes-data-sync_OsDisk_1_6805966503c542b78dbe9ad597d363d0** (West Europe, IGENOMES-DATA-SYNC_GROUP)

### Images

#### Bastion Images

- **bastion.20240320111435** (West Europe, nf-nomad-dev-rg)
- **bastion.20240529125052** (West Europe, nf-nomad-dev-rg)
- **bastion.20240603130052** (West Europe, nf-nomad-dev-rg)

#### Hashistack Images

- **hashistack.20240320121559** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240320122410** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240320141508** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240320150510** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240320152709** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240320161553** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240320163511** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240322140155** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240322151338** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240325143604** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240326122214** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240603131113** (West Europe, nf-nomad-dev-rg)
- **hashistack.20240607112210** (West Europe, nf-nomad-dev-rg)
- **hashistack.20241106143509** (West Europe, nf-nomad-dev-rg)
- **hashistack.20241106160129** (West Europe, nf-nomad-dev-rg)

### Storage Accounts

- **nfcoreazuremegatests** (West Europe, nf-core-azure-megatests)
- **nfnomad** (West Europe, nf-nomad-dev-rg)

### Other Resources

- **nfcoreazuremegatests** - Batch account (West Europe, nf-core-azure-megatests)
- **nfcoreazuremegatests** - Container registry (West Europe, nf-core-azure-megatests)
- **igenomes-data-sync_key** - SSH key (West Europe, igenomes-data-sync_group)

### Resource Groups

- **nf-nomad-dev-rg** - Main development environment for Nomad cluster
- **igenomes-data-sync_group** - Data synchronization resources
- **nf-core-azure-megatests** - Testing infrastructure

### Summary

- **Total VMs**: 8 (1 bastion server, 6 hashistack nodes, 1 data sync server)
- **Total Images**: 18 (3 bastion snapshots, 15 hashistack snapshots)
- **Total Disks**: 8 (OS disks for each VM)
- **Total Storage Accounts**: 2
- **Resource Groups**: 3
