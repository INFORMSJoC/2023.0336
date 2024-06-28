[![INFORMS Journal on Computing Logo](https://INFORMSJoC.github.io/logos/INFORMS_Journal_on_Computing_Header.jpg)](https://pubsonline.informs.org/journal/ijoc)

# Microgrid Planner

This archive is distributed in association with the [INFORMS Journal on
Computing](https://pubsonline.informs.org/journal/ijoc) under the [MIT License](LICENSE).

The software and data in this repository are a snapshot of the software and data
that were used in the research reported on in the paper 
[Microgrid Planner: An Open-Source Software Platform](https://doi.org/10.1287/ijoc.2023.0336) by D. Reich and L. Frye. 
The snapshot is based on 
[this SHA](https://github.com/reichd/MicrogridPlanner/commit/92b32b0d757621087b9f15516cef3c9360ffc2f0) 
in the development repository.

**Important: This code is being developed on an on-going basis at 
https://github.com/reichd/MicrogridPlanner. Please go there if you would like to
get a more recent version or you would like to request support.**

## Cite

To cite the contents of this repository, please cite both the paper "Microgrid Planner: An Open-Source Software Platform" and this repo, using their respective DOIs.

https://doi.org/10.1287/ijoc.2023.0336

https://doi.org/10.1287/ijoc.2023.0336.cd

Below is the BibTex for citing this snapshot of the repository.

```
@misc{MicrogridPlanner,
  author =        {Reich, Daniel and Frye, Leah},
  publisher =     {INFORMS Journal on Computing},
  title =         {{Microgrid Planner}},
  year =          {2024},
  doi =           {10.1287/ijoc.2023.0336.cd},
  url =           {https://github.com/INFORMSJoC/2023.0336},
  note =          {Available for download at https://github.com/INFORMSJoC/2023.0336},
}  
```

## Description

The goal of this software is to deploy analytical methods for microgrid planning.

## File Organization

    ├── backend                                 <- Backend application (see README in backend for more info)
    ├── frontend                                <- Frontend application (see README in fronted for more info)
    ├── config.ini.template                     <- Global config file template for shared settings between backend and frontend (copy to config.ini and update parameter values)
    ├── database-authentication.env.template    <- MySQL configuration file template for authentication database (copy to database-authentication.env and update parameter values)
    ├── docker-compose.yaml.template            <- Configuration file for Docker multi-container application services (copy to docker-compose.yaml)
    ├── generate_secret_key.py                  <- Script to generate a secret key for config.ini
    ├── LICENSE                                 <- License terms
    └── README                                  <- Documentation


## Instructions to Run Locally

1. Setup a **Python 3.11** environment for the backend and the frontend
    - On Windows
      - Make sure to check "Add Python to environment variables" under advanced options in setup
    
2. Install **mysql**, add it to `${PATH}` and ensure it is running in the background
    - On Mac OS
        - install homebrew
        - run `brew install pkg-config`
        - run `brew install mysql`
        - run `brew install mysql-client`
        - run `echo 'export PATH="/usr/local/opt/mysql-client/bin:$PATH"' >> ~/.zshrc`
        - run `export LDFLAGS="-L/usr/local/opt/mysql-client/lib"`
        - run `export CPPFLAGS="-I/usr/local/opt/mysql-client/include"`
    - On Windows (with local admin)
        - Install [MySQL Server for Windows](https://dev.mysql.com/downloads/installer/) (choose `mysql-installer-community-8.0.360.msi`)
        - Run the installer and step through the installation options. Choose `Server only` as the setup type. 
        - Once the install is complete, you'll need to configure the server. Use the default options and click `next`.
        - Choose `Use Strong Password Encryption for Authentication` for the authentication method
        - Create the root password and **save it**. It will be used in the `database-*.env` files.
        - Keep the default `Windows Service` options and click `next`.
        - Under `Apply Configuration` click `Execute`.
        - Continue through the next steps using the default options
        - The server should now be running. If you need to start the server again, go to `Services` > `MySQL80` and click `start`.
        - For troubleshooting, read the [MySQL documentation for installing via the Windows installer](https://dev.mysql.com/doc/refman/8.3/en/windows-installation.html).
    - On Windows (without local admin)
        - Install [MySQL Server .zip version 8](https://dev.mysql.com/downloads/mysql/) (select `Windows (x86, 64-bit), ZIP Archive`).
        - Extract the files and move the folder to your programs folder (ex: `C:\Program Files\MySQL\mysql8install`)
        - Inside the `MySQL` folder, create two empty directories: `logs` and `mysqldata`.
        - Inside the `mysql` install folder that contains `bin`, `docs`, `include`, etc., create a new file called `my.ini`.
        - Open `my.ini` in an editor and paste the following, correcting the paths to your `mysqlinstall`, `mysqldata`, and `mysql` logs folders:
            ```
            [mysqld]
            basedir = "C:/MYSQL/mysql8install"
            datadir = "C:/MYSQL/mysqldata"
            tmpdir = "C:/MYSQL/logs"
            log-error = "C:/MYSQL/mysql-server-1.log"
            ```     
        - Open a terminal and navigate to your `MySql/mysql8install/bin` folder.
        - Run `mysqld --initialize-insecure` to initialize the data. This will create a data folder under `/mysql8install`. Running it as insecure will enable running the database without a password.
        - In the same directory, run `mysqld --console` to start the MySQL server. Leave this terminal window open. Closing it will stop the server. 
        - For troubleshooting, read the [MySQL documentation for installing via archive](https://dev.mysql.com/doc/mysql-installation-excerpt/5.7/en/windows-install-archive.html).


## Instructions to Run Locally or Deploy via Docker

1. Create configuration files, per instructions below
    - `config.ini`
        - Generate `SECRET_KEY` by running `python3 generate_secret_key.py`
        - Note: password values in `backend/data/mysql/*data*.sql` are stored in plain text and are automatically hashed with this secret key when the authentication database is created
    - `database-authentication.env`
        - `MYSQL_ROOT_PASSWORD` may be set when setting up the MYSQL database in step 2 above 
        - `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DATABASE` can be set to any values
        - `MYSQL_PORT` should be set to `3306`
        - `MYSQL_HOST` should be set to `127.0.0.1` or `localhost` or when running Docker to `mysql`
2. Review `README` files in both `frontend` and `backend` folders and follow instructions.


## Instructions to Deploy via Docker

1. Run `docker-compose up` (by default, Docker will run the docker-compose.yaml file)
