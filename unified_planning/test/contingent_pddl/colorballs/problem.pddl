(define (problem colorballs-10-1)
(:domain colorballs)

 (:objects
    o1
   - obj

    p1-1
    p1-2
    p1-3
    p1-4
    p1-5
    p1-6
    p1-7
    p1-8
    p1-9
    p1-10
    p2-1
    p2-2
    p2-3
    p2-4
    p2-5
    p2-6
    p2-7
    p2-8
    p2-9
    p2-10
    p3-1
    p3-2
    p3-3
    p3-4
    p3-5
    p3-6
    p3-7
    p3-8
    p3-9
    p3-10
    p4-1
    p4-2
    p4-3
    p4-4
    p4-5
    p4-6
    p4-7
    p4-8
    p4-9
    p4-10
    p5-1
    p5-2
    p5-3
    p5-4
    p5-5
    p5-6
    p5-7
    p5-8
    p5-9
    p5-10
    p6-1
    p6-2
    p6-3
    p6-4
    p6-5
    p6-6
    p6-7
    p6-8
    p6-9
    p6-10
    p7-1
    p7-2
    p7-3
    p7-4
    p7-5
    p7-6
    p7-7
    p7-8
    p7-9
    p7-10
    p8-1
    p8-2
    p8-3
    p8-4
    p8-5
    p8-6
    p8-7
    p8-8
    p8-9
    p8-10
    p9-1
    p9-2
    p9-3
    p9-4
    p9-5
    p9-6
    p9-7
    p9-8
    p9-9
    p9-10
    p10-1
    p10-2
    p10-3
    p10-4
    p10-5
    p10-6
    p10-7
    p10-8
    p10-9
    p10-10
   - pos

    red
    blue
    purple
    green
   - col

    t1
    t2
    t3
    t4
   - gar

    )
   (:init
    (and
     (at p5-5)
    (garbage-at t1 p1-1)
    (garbage-at t2 p1-10)
    (garbage-at t3 p10-1)
    (garbage-at t4 p10-10)
    (garbage-color t1 red)
    (garbage-color t2 blue)
    (garbage-color t3 green)
    (garbage-color t4 purple)

     (adj p1-1 p2-1)
     (adj p2-1 p1-1)

     (adj p1-2 p2-2)
     (adj p2-2 p1-2)

     (adj p1-3 p2-3)
     (adj p2-3 p1-3)

     (adj p1-4 p2-4)
     (adj p2-4 p1-4)

     (adj p1-5 p2-5)
     (adj p2-5 p1-5)

     (adj p1-6 p2-6)
     (adj p2-6 p1-6)

     (adj p1-7 p2-7)
     (adj p2-7 p1-7)

     (adj p1-8 p2-8)
     (adj p2-8 p1-8)

     (adj p1-9 p2-9)
     (adj p2-9 p1-9)

     (adj p1-10 p2-10)
     (adj p2-10 p1-10)

     (adj p2-1 p3-1)
     (adj p3-1 p2-1)

     (adj p2-2 p3-2)
     (adj p3-2 p2-2)

     (adj p2-3 p3-3)
     (adj p3-3 p2-3)

     (adj p2-4 p3-4)
     (adj p3-4 p2-4)

     (adj p2-5 p3-5)
     (adj p3-5 p2-5)

     (adj p2-6 p3-6)
     (adj p3-6 p2-6)

     (adj p2-7 p3-7)
     (adj p3-7 p2-7)

     (adj p2-8 p3-8)
     (adj p3-8 p2-8)

     (adj p2-9 p3-9)
     (adj p3-9 p2-9)

     (adj p2-10 p3-10)
     (adj p3-10 p2-10)

     (adj p3-1 p4-1)
     (adj p4-1 p3-1)

     (adj p3-2 p4-2)
     (adj p4-2 p3-2)

     (adj p3-3 p4-3)
     (adj p4-3 p3-3)

     (adj p3-4 p4-4)
     (adj p4-4 p3-4)

     (adj p3-5 p4-5)
     (adj p4-5 p3-5)

     (adj p3-6 p4-6)
     (adj p4-6 p3-6)

     (adj p3-7 p4-7)
     (adj p4-7 p3-7)

     (adj p3-8 p4-8)
     (adj p4-8 p3-8)

     (adj p3-9 p4-9)
     (adj p4-9 p3-9)

     (adj p3-10 p4-10)
     (adj p4-10 p3-10)

     (adj p4-1 p5-1)
     (adj p5-1 p4-1)

     (adj p4-2 p5-2)
     (adj p5-2 p4-2)

     (adj p4-3 p5-3)
     (adj p5-3 p4-3)

     (adj p4-4 p5-4)
     (adj p5-4 p4-4)

     (adj p4-5 p5-5)
     (adj p5-5 p4-5)

     (adj p4-6 p5-6)
     (adj p5-6 p4-6)

     (adj p4-7 p5-7)
     (adj p5-7 p4-7)

     (adj p4-8 p5-8)
     (adj p5-8 p4-8)

     (adj p4-9 p5-9)
     (adj p5-9 p4-9)

     (adj p4-10 p5-10)
     (adj p5-10 p4-10)

     (adj p5-1 p6-1)
     (adj p6-1 p5-1)

     (adj p5-2 p6-2)
     (adj p6-2 p5-2)

     (adj p5-3 p6-3)
     (adj p6-3 p5-3)

     (adj p5-4 p6-4)
     (adj p6-4 p5-4)

     (adj p5-5 p6-5)
     (adj p6-5 p5-5)

     (adj p5-6 p6-6)
     (adj p6-6 p5-6)

     (adj p5-7 p6-7)
     (adj p6-7 p5-7)

     (adj p5-8 p6-8)
     (adj p6-8 p5-8)

     (adj p5-9 p6-9)
     (adj p6-9 p5-9)

     (adj p5-10 p6-10)
     (adj p6-10 p5-10)

     (adj p6-1 p7-1)
     (adj p7-1 p6-1)

     (adj p6-2 p7-2)
     (adj p7-2 p6-2)

     (adj p6-3 p7-3)
     (adj p7-3 p6-3)

     (adj p6-4 p7-4)
     (adj p7-4 p6-4)

     (adj p6-5 p7-5)
     (adj p7-5 p6-5)

     (adj p6-6 p7-6)
     (adj p7-6 p6-6)

     (adj p6-7 p7-7)
     (adj p7-7 p6-7)

     (adj p6-8 p7-8)
     (adj p7-8 p6-8)

     (adj p6-9 p7-9)
     (adj p7-9 p6-9)

     (adj p6-10 p7-10)
     (adj p7-10 p6-10)

     (adj p7-1 p8-1)
     (adj p8-1 p7-1)

     (adj p7-2 p8-2)
     (adj p8-2 p7-2)

     (adj p7-3 p8-3)
     (adj p8-3 p7-3)

     (adj p7-4 p8-4)
     (adj p8-4 p7-4)

     (adj p7-5 p8-5)
     (adj p8-5 p7-5)

     (adj p7-6 p8-6)
     (adj p8-6 p7-6)

     (adj p7-7 p8-7)
     (adj p8-7 p7-7)

     (adj p7-8 p8-8)
     (adj p8-8 p7-8)

     (adj p7-9 p8-9)
     (adj p8-9 p7-9)

     (adj p7-10 p8-10)
     (adj p8-10 p7-10)

     (adj p8-1 p9-1)
     (adj p9-1 p8-1)

     (adj p8-2 p9-2)
     (adj p9-2 p8-2)

     (adj p8-3 p9-3)
     (adj p9-3 p8-3)

     (adj p8-4 p9-4)
     (adj p9-4 p8-4)

     (adj p8-5 p9-5)
     (adj p9-5 p8-5)

     (adj p8-6 p9-6)
     (adj p9-6 p8-6)

     (adj p8-7 p9-7)
     (adj p9-7 p8-7)

     (adj p8-8 p9-8)
     (adj p9-8 p8-8)

     (adj p8-9 p9-9)
     (adj p9-9 p8-9)

     (adj p8-10 p9-10)
     (adj p9-10 p8-10)

     (adj p9-1 p10-1)
     (adj p10-1 p9-1)

     (adj p9-2 p10-2)
     (adj p10-2 p9-2)

     (adj p9-3 p10-3)
     (adj p10-3 p9-3)

     (adj p9-4 p10-4)
     (adj p10-4 p9-4)

     (adj p9-5 p10-5)
     (adj p10-5 p9-5)

     (adj p9-6 p10-6)
     (adj p10-6 p9-6)

     (adj p9-7 p10-7)
     (adj p10-7 p9-7)

     (adj p9-8 p10-8)
     (adj p10-8 p9-8)

     (adj p9-9 p10-9)
     (adj p10-9 p9-9)

     (adj p9-10 p10-10)
     (adj p10-10 p9-10)


     (adj p1-1 p1-2)
     (adj p1-2 p1-1)

     (adj p2-1 p2-2)
     (adj p2-2 p2-1)

     (adj p3-1 p3-2)
     (adj p3-2 p3-1)

     (adj p4-1 p4-2)
     (adj p4-2 p4-1)

     (adj p5-1 p5-2)
     (adj p5-2 p5-1)

     (adj p6-1 p6-2)
     (adj p6-2 p6-1)

     (adj p7-1 p7-2)
     (adj p7-2 p7-1)

     (adj p8-1 p8-2)
     (adj p8-2 p8-1)

     (adj p9-1 p9-2)
     (adj p9-2 p9-1)

     (adj p10-1 p10-2)
     (adj p10-2 p10-1)

     (adj p1-2 p1-3)
     (adj p1-3 p1-2)

     (adj p2-2 p2-3)
     (adj p2-3 p2-2)

     (adj p3-2 p3-3)
     (adj p3-3 p3-2)

     (adj p4-2 p4-3)
     (adj p4-3 p4-2)

     (adj p5-2 p5-3)
     (adj p5-3 p5-2)

     (adj p6-2 p6-3)
     (adj p6-3 p6-2)

     (adj p7-2 p7-3)
     (adj p7-3 p7-2)

     (adj p8-2 p8-3)
     (adj p8-3 p8-2)

     (adj p9-2 p9-3)
     (adj p9-3 p9-2)

     (adj p10-2 p10-3)
     (adj p10-3 p10-2)

     (adj p1-3 p1-4)
     (adj p1-4 p1-3)

     (adj p2-3 p2-4)
     (adj p2-4 p2-3)

     (adj p3-3 p3-4)
     (adj p3-4 p3-3)

     (adj p4-3 p4-4)
     (adj p4-4 p4-3)

     (adj p5-3 p5-4)
     (adj p5-4 p5-3)

     (adj p6-3 p6-4)
     (adj p6-4 p6-3)

     (adj p7-3 p7-4)
     (adj p7-4 p7-3)

     (adj p8-3 p8-4)
     (adj p8-4 p8-3)

     (adj p9-3 p9-4)
     (adj p9-4 p9-3)

     (adj p10-3 p10-4)
     (adj p10-4 p10-3)

     (adj p1-4 p1-5)
     (adj p1-5 p1-4)

     (adj p2-4 p2-5)
     (adj p2-5 p2-4)

     (adj p3-4 p3-5)
     (adj p3-5 p3-4)

     (adj p4-4 p4-5)
     (adj p4-5 p4-4)

     (adj p5-4 p5-5)
     (adj p5-5 p5-4)

     (adj p6-4 p6-5)
     (adj p6-5 p6-4)

     (adj p7-4 p7-5)
     (adj p7-5 p7-4)

     (adj p8-4 p8-5)
     (adj p8-5 p8-4)

     (adj p9-4 p9-5)
     (adj p9-5 p9-4)

     (adj p10-4 p10-5)
     (adj p10-5 p10-4)

     (adj p1-5 p1-6)
     (adj p1-6 p1-5)

     (adj p2-5 p2-6)
     (adj p2-6 p2-5)

     (adj p3-5 p3-6)
     (adj p3-6 p3-5)

     (adj p4-5 p4-6)
     (adj p4-6 p4-5)

     (adj p5-5 p5-6)
     (adj p5-6 p5-5)

     (adj p6-5 p6-6)
     (adj p6-6 p6-5)

     (adj p7-5 p7-6)
     (adj p7-6 p7-5)

     (adj p8-5 p8-6)
     (adj p8-6 p8-5)

     (adj p9-5 p9-6)
     (adj p9-6 p9-5)

     (adj p10-5 p10-6)
     (adj p10-6 p10-5)

     (adj p1-6 p1-7)
     (adj p1-7 p1-6)

     (adj p2-6 p2-7)
     (adj p2-7 p2-6)

     (adj p3-6 p3-7)
     (adj p3-7 p3-6)

     (adj p4-6 p4-7)
     (adj p4-7 p4-6)

     (adj p5-6 p5-7)
     (adj p5-7 p5-6)

     (adj p6-6 p6-7)
     (adj p6-7 p6-6)

     (adj p7-6 p7-7)
     (adj p7-7 p7-6)

     (adj p8-6 p8-7)
     (adj p8-7 p8-6)

     (adj p9-6 p9-7)
     (adj p9-7 p9-6)

     (adj p10-6 p10-7)
     (adj p10-7 p10-6)

     (adj p1-7 p1-8)
     (adj p1-8 p1-7)

     (adj p2-7 p2-8)
     (adj p2-8 p2-7)

     (adj p3-7 p3-8)
     (adj p3-8 p3-7)

     (adj p4-7 p4-8)
     (adj p4-8 p4-7)

     (adj p5-7 p5-8)
     (adj p5-8 p5-7)

     (adj p6-7 p6-8)
     (adj p6-8 p6-7)

     (adj p7-7 p7-8)
     (adj p7-8 p7-7)

     (adj p8-7 p8-8)
     (adj p8-8 p8-7)

     (adj p9-7 p9-8)
     (adj p9-8 p9-7)

     (adj p10-7 p10-8)
     (adj p10-8 p10-7)

     (adj p1-8 p1-9)
     (adj p1-9 p1-8)

     (adj p2-8 p2-9)
     (adj p2-9 p2-8)

     (adj p3-8 p3-9)
     (adj p3-9 p3-8)

     (adj p4-8 p4-9)
     (adj p4-9 p4-8)

     (adj p5-8 p5-9)
     (adj p5-9 p5-8)

     (adj p6-8 p6-9)
     (adj p6-9 p6-8)

     (adj p7-8 p7-9)
     (adj p7-9 p7-8)

     (adj p8-8 p8-9)
     (adj p8-9 p8-8)

     (adj p9-8 p9-9)
     (adj p9-9 p9-8)

     (adj p10-8 p10-9)
     (adj p10-9 p10-8)

     (adj p1-9 p1-10)
     (adj p1-10 p1-9)

     (adj p2-9 p2-10)
     (adj p2-10 p2-9)

     (adj p3-9 p3-10)
     (adj p3-10 p3-9)

     (adj p4-9 p4-10)
     (adj p4-10 p4-9)

     (adj p5-9 p5-10)
     (adj p5-10 p5-9)

     (adj p6-9 p6-10)
     (adj p6-10 p6-9)

     (adj p7-9 p7-10)
     (adj p7-10 p7-9)

     (adj p8-9 p8-10)
     (adj p8-10 p8-9)

     (adj p9-9 p9-10)
     (adj p9-10 p9-9)

     (adj p10-9 p10-10)
     (adj p10-10 p10-9)


     (oneof
        (obj-at o1 p1-2)
        (obj-at o1 p1-3)
        (obj-at o1 p1-4)
        (obj-at o1 p1-5)
        (obj-at o1 p1-6)
        (obj-at o1 p1-7)
        (obj-at o1 p1-8)
        (obj-at o1 p1-9)
        (obj-at o1 p2-1)
        (obj-at o1 p2-2)
        (obj-at o1 p2-3)
        (obj-at o1 p2-4)
        (obj-at o1 p2-5)
        (obj-at o1 p2-6)
        (obj-at o1 p2-7)
        (obj-at o1 p2-8)
        (obj-at o1 p2-9)
        (obj-at o1 p2-10)
        (obj-at o1 p3-1)
        (obj-at o1 p3-2)
        (obj-at o1 p3-3)
        (obj-at o1 p3-4)
        (obj-at o1 p3-5)
        (obj-at o1 p3-6)
        (obj-at o1 p3-7)
        (obj-at o1 p3-8)
        (obj-at o1 p3-9)
        (obj-at o1 p3-10)
        (obj-at o1 p4-1)
        (obj-at o1 p4-2)
        (obj-at o1 p4-3)
        (obj-at o1 p4-4)
        (obj-at o1 p4-5)
        (obj-at o1 p4-6)
        (obj-at o1 p4-7)
        (obj-at o1 p4-8)
        (obj-at o1 p4-9)
        (obj-at o1 p4-10)
        (obj-at o1 p5-1)
        (obj-at o1 p5-2)
        (obj-at o1 p5-3)
        (obj-at o1 p5-4)
        (obj-at o1 p5-5)
        (obj-at o1 p5-6)
        (obj-at o1 p5-7)
        (obj-at o1 p5-8)
        (obj-at o1 p5-9)
        (obj-at o1 p5-10)
        (obj-at o1 p6-1)
        (obj-at o1 p6-2)
        (obj-at o1 p6-3)
        (obj-at o1 p6-4)
        (obj-at o1 p6-5)
        (obj-at o1 p6-6)
        (obj-at o1 p6-7)
        (obj-at o1 p6-8)
        (obj-at o1 p6-9)
        (obj-at o1 p6-10)
        (obj-at o1 p7-1)
        (obj-at o1 p7-2)
        (obj-at o1 p7-3)
        (obj-at o1 p7-4)
        (obj-at o1 p7-5)
        (obj-at o1 p7-6)
        (obj-at o1 p7-7)
        (obj-at o1 p7-8)
        (obj-at o1 p7-9)
        (obj-at o1 p7-10)
        (obj-at o1 p8-1)
        (obj-at o1 p8-2)
        (obj-at o1 p8-3)
        (obj-at o1 p8-4)
        (obj-at o1 p8-5)
        (obj-at o1 p8-6)
        (obj-at o1 p8-7)
        (obj-at o1 p8-8)
        (obj-at o1 p8-9)
        (obj-at o1 p8-10)
        (obj-at o1 p9-1)
        (obj-at o1 p9-2)
        (obj-at o1 p9-3)
        (obj-at o1 p9-4)
        (obj-at o1 p9-5)
        (obj-at o1 p9-6)
        (obj-at o1 p9-7)
        (obj-at o1 p9-8)
        (obj-at o1 p9-9)
        (obj-at o1 p9-10)
        (obj-at o1 p10-2)
        (obj-at o1 p10-3)
        (obj-at o1 p10-4)
        (obj-at o1 p10-5)
        (obj-at o1 p10-6)
        (obj-at o1 p10-7)
        (obj-at o1 p10-8)
        (obj-at o1 p10-9)
     )

     (oneof
       (color o1 red)
       (color o1 blue)
       (color o1 green)
       (color o1 purple)
     )


    )
    )
    (:goal (trashed o1)))
