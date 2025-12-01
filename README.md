# EVisor---Backend---RnD
## 🔥Connect to Server RnD
**IP: 192.168.54.39**  
**Username: RnD**  
**Password:** <_default_>  
**Required:**  
- Be on the same network layer. You can use a VPN to route your home network into the ESTEC network. For example, your IP should be in the range 192.168.54.xxx.
- File .env key to deploy. 
### Method 1: Connect with Remote Desktop (Using GUI)
Open **Remote Desktop Connection** on your machine with IP is **192.168.54.39**. User name is **rnd** or **RnD** and type Password.
### Method 2: Connect with Visual Studio Code (Only develope with code)
Install **Remote - SSH** extensions and configure:
```bash
ssh -i rnd@192.168.54.39
```
Type Password.
## 🚀 Deployment on Server
### 🚧Git clone:
```bash
git clone https://github.com/estec-digital/EVisor---Backend---RnD.git
cd EVisor---Backend---RnD
```
### 🐧Linux:
```bash
virtualenv venv 
source .\venv\bin\activate
pip install -r requirements.txt
```
### 🪟Windows:
```bash
virtualenv venv 
.\venv\Scripts\activate
pip install -r requirements.txt
```
## 🏁Start BackEnd on Server
### Build Docker Compose for Database:
Look at the repo, you can see a file with name **docker-compose.yaml**. Let's open terminal and type:
```bash
docker compose up -d
```
to build microservices. Database: PostgreSQL. Bucket Storage: MinIO...
### 🌱Develop:
Start service on a specific port, the service running **on terminal** with auto reload.
```bash
uvicorn src.main:app --port ${PORT} --host ${HOST} --reload
```
- _**Example:** uvicorn src.main:app --port 8000 --host 0.0.0.0 --reload_
### 🌴Deploy:
Start service on a specific port, the service running **on background** and no hang up (nohup). Only apply for Linux OS.
```bash
nohup uvicorn src.main:app --port ${PORT} --host ${HOST} &
```
- _**Example:** nohup uvicorn src.main:app --port 8000 --host 0.0.0.0 &_  

Check if the service is running to see the process id **PID**.
```bash
ps aux | grep ${PORT}
```
- _**Example:** ps aux | grep 8000_  

Kill the ML service process with **PID**.
```bash
kill -9 ${PID}
```
- _**Example:** kill -9 1234_  

## 🦾Swagger APIs from your local machine
To check if the service is alive on localhost, go here:  
**http://localhost:8000/docs**  
To check if the service is alive on Domain/Private, go here:  
**http://192.168.54.39:8000/docs**  
To check if the service is alive on Public, go here:  
**http://113.160.226.217:8001/docs**  
