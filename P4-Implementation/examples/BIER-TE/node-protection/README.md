Simple example toplogy for Bier-TE-FRR node protection.
    
```   
   h1                 broken             h3
    \     6        5    // 8        7    /
    (s1) ------------ (s2) ---------- (s3)
      \ 10             //|             / 14
       \                 |12          /
        \                |           /
         \               |          /
          \              |         /
           \             |11      /
            \         9  |       /
             ---------- (s4) --- 13
                         |
                         h4 

```                                  

Send mc packet from h1 to h4 and h3 using the patch 6,8,12. Backup path is 10, 13.

BTAFT of s1:

| Failed bit (FB) | Downstream bit (DB) | Add bits (AB) | Reset bits (RB) |
|:---------------:|:-------------------:|---------------|-----------------|
|        6        |          8          |    3 10 13    |       8 13      |
|        6        |          12         |      4 10     |     10 12 14    |
|        6        |          2          |    2 10 11    |        -        |
|        10       |          11         |      2 6      |      6 7 11     |
|        10       |          13         |     3 6 8     |       8 13      |
|        10       |          4          |    4 6 12     |        -        |