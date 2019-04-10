```
                                   Layer 3 adjacency 
                          ====================================
   h1                   6//                                   \\      
    \   4             5  ||                                    \\  7   
   (s1) --------------- (s2) -------------- (s3) --------------- (s4) - h4
3 (0:0100)               \ 8                                  1 (0:0001)   
                          \ 9                 
                         (s5)               
                     2 (0:0010)        
                          /                    					    	                  
                         h2                   
```

Send bier-te packet from s1 to s5 and s4 with a non bier capable device (s3) using an ip tunnel.
