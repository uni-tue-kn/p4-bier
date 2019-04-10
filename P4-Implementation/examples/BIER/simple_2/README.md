Simple example toplogy.
    
```
      h1         h3 
       \         /
      (s1) ---- (s3) 
  1 (0:0001)  3 (0:0100)
        \      /
         \    /
          \  /  
         (s2)
       2 (0:0010)
          /
         h2
```                                    

Send mc packet from h1->s3, s3->h3, s3->s2, s2->h2. 