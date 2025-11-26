@echo off
mkdir data\raw\AMI 2>nul
> data\raw\AMI\ES2002a.txt echo PM: Can you send the sales deck to the client by Friday?
>> data\raw\AMI\ES2002a.txt echo DEV: I will finalize slides and email them tomorrow.
>> data\raw\AMI\ES2002a.txt echo QA: We need to verify figures before EOD.
>> data\raw\AMI\ES2002a.txt echo PM: John, please work on the pricing model and share by next Tuesday.
>> data\raw\AMI\ES2002a.txt echo DEV: Can you, Anna, draft the summary notes today?
>> data\raw\AMI\ES2002a.txt echo QA: I can review the numbers by Monday morning.
> data\raw\AMI\roles.csv echo speaker,role
>> data\raw\AMI\roles.csv echo PM,Project Manager
>> data\raw\AMI\roles.csv echo DEV,Developer
>> data\raw\AMI\roles.csv echo QA,Quality Analyst
echo Sample AMI-style files created.
