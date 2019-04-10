Example from RFC-8279 6.3 Page 18
    
```
   h1                                                              h4
    \                                                              /
   (s1) --------------- (s2) -------------- (s3) --------------- (s4)
4 (0:1000)               \                   \               1 (0:0001)   
                          \                   \ 
                         (s5)                (s6)
                      3 (0:0100)         2 (0:0010)
                          /                    /					    	                  
                         h2                   h3 

```

Send mc packet from h1 to h2 and h4 using BIER.