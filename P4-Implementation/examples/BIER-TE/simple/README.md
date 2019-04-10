Simple example toplogy.
    
```
      h1                 h3 
       \    4        5   / 
      (s1) ----------- (s3) 
    (0:0001)          (0:0100)
      6 \            / 7
         \          /
          \        / 
       9   \      / 8
             (s2)
           (0:0010)
              | 
              h2
```                                    

Send mc packet from h1->s1->s2->s3->h3 using BIER-TE and the links 6->8. BitString should be 010100100.