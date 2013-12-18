newRHELic
=========

A RHEL/CentOS-centric plugin for New Relic Monitoring App

Installation
------------
* RPM
    * Dowload the source and execute:  

    ```
    python setup.py sdist_rpm
    cd dist/
    rpm -ivh <RPM You Just Made>.rpm / yum install <RPM You Just Made>.rpm
    ```  
    
    *Obviously you only have to use rpm OR yum (not both), and you only have to make the RPM for each architecture you're using.

* Source Distribution
    * Download the source and execute:  

    ```
    python setup.py sdist
    cd dist/
    tar zxf <The Tarball>
    cd <The Directory you just unzipped>
    python setup.py install
    ```  

    * Obviously you can move that tarball around after creating it once.
