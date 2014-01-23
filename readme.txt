1.ubuntu13.10 & Python3.3.2 & Flask 0.10.1 & Pymongo & Apache2
2.Copy infosrv folder into /var/www/
3.sudo chown -R www-data:www-data /var/www/infosrv
4.Copy infosrv.conf into /etc/apache2/sites-avaiable and, then run commend 'sudo a2ensite infosrv.conf'
5.Edit infosrv.py 'app.run('192.168.1.109')' ==> 'app.run()'
6.Modifying /etc/apache2/enwars two parameters
    export LANG='zh_TW.UTF-8
    export_LC_ALL='zh_TW.UTF-8'
7.reboot system