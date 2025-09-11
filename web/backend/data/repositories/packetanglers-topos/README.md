# Sample Container Lab Topologies

```bash
# Clone this repo to Linux VM where ContainerLab and Docker is running
git clone https://github.com/PacketAnglers/clab-topos.git
```

```bash
# Start a topology
sudo clab deploy -t clab-topos/atd-dc/atd-dc.yml --reconfigure
```

```bash
# Stop a topology
sudo clab destroy -t clab-topos/atd-dc/atd-dc.yml
```

## Connecting to Hosts

Username: admin
Password: admin

```bash
# Log into SPINE1
ssh admin@172.100.100.101

# Or connect directly via Docker
docker exec -it SPINE1 Cli
```