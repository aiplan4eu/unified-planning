


(define (problem mixed-f4-p2-u20-v5-g5-a60-n10-A20-B80-N50-F5-r4)
   (:domain miconic)
(:objects
             p0 p1 - passenger
             f0 f1 f2 f3 - floor)


(:init
(above f0 f1)
(above f0 f2)
(above f0 f3)

(above f1 f2)
(above f1 f3)

(above f2 f3)



(origin p0 f3)
(destin p0 f2)

(origin p1 f2)
(destin p1 f0)






(lift-at f0)
)


(:goal (forall (?p - passenger) (served ?p)))
)


