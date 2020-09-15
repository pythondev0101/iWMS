@echo off

D:\BarTender\Bartend.EXE /F=D:\BARCODE\GRMBarcode.btw /p /x

set /A "X = 0"
:TimerX
set /A "X = %X% +1"
if %X% == 50 goto DELFILE

DELFILE
del /s /q "D:\iWMS\app\iwms\pallet_tag\barcodetxtfile.*"


