Simple example toplogy for Bier-TE-FRR.
    
```
   h1                                h2
    \     8       failed        7    /
    (s1) ----------//----------- (s2) 
     | 6                           | 11
     |                             |
     |                             |
     | 5                           | 12
    (s3) ------------------------ (s4)
    /    9                      10
   h3
```                                    

Send mc packet from h1 to h2 and h3. Backup-Path for failed adjacencies 8 is 6->9->12.