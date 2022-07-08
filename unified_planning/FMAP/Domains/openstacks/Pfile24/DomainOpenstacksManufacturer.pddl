(define (domain openstacks)
(:requirements :typing :equality :fluents)
(:types
    order product count - object)
(:constants
 p1 p2 p3 p4 p5 p6 p7 p8 p9 p10 p11 p12 p13 p14 p15 p16 p17 p18 p19 p20 p21 p22 p23 p24 p25 p26 p27 p28 - product
 o1 o2 o3 o4 o5 o6 o7 o8 o9 o10 o11 o12 o13 o14 o15 o16 o17 o18 o19 o20 o21 o22 o23 o24 o25 o26 o27 o28 - order
)
(:predicates
  (includes ?o - order ?p - product)
  (waiting ?o - order)
  (started ?o - order)
  (shipped ?o - order)
  (made ?p - product))
(:functions
  (stacks-avail) - count
  (next-count ?s) - count)
(:action open-new-stack
 :parameters (?open ?new-open - count)
 :precondition (and (= (stacks-avail) ?open) (= (next-count ?open) ?new-open))
 :effect (assign (stacks-avail) ?new-open))
(:action make-product-p1
 :parameters ()
 :precondition (and
(not (made p1))
(started o7)
(started o9)
)
 :effect (and
(made p1)
))
(:action make-product-p2
 :parameters ()
 :precondition (and
(not (made p2))
(started o6)
)
 :effect (and
(made p2)
))
(:action make-product-p3
 :parameters ()
 :precondition (and
(not (made p3))
(started o10)
(started o19)
)
 :effect (and
(made p3)
))
(:action make-product-p4
 :parameters ()
 :precondition (and
(not (made p4))
(started o5)
)
 :effect (and
(made p4)
))
(:action make-product-p5
 :parameters ()
 :precondition (and
(not (made p5))
(started o27)
)
 :effect (and
(made p5)
))
(:action make-product-p6
 :parameters ()
 :precondition (and
(not (made p6))
(started o9)
(started o25)
)
 :effect (and
(made p6)
))
(:action make-product-p7
 :parameters ()
 :precondition (and
(not (made p7))
(started o8)
)
 :effect (and
(made p7)
))
(:action make-product-p8
 :parameters ()
 :precondition (and
(not (made p8))
(started o12)
(started o13)
(started o16)
)
 :effect (and
(made p8)
))
(:action make-product-p9
 :parameters ()
 :precondition (and
(not (made p9))
(started o25)
)
 :effect (and
(made p9)
))
(:action make-product-p10
 :parameters ()
 :precondition (and
(not (made p10))
(started o18)
)
 :effect (and
(made p10)
))
(:action make-product-p11
 :parameters ()
 :precondition (and
(not (made p11))
(started o20)
(started o22)
(started o24)
)
 :effect (and
(made p11)
))
(:action make-product-p12
 :parameters ()
 :precondition (and
(not (made p12))
(started o4)
(started o12)
(started o14)
(started o22)
(started o24)
)
 :effect (and
(made p12)
))
(:action make-product-p13
 :parameters ()
 :precondition (and
(not (made p13))
(started o11)
(started o15)
)
 :effect (and
(made p13)
))
(:action make-product-p14
 :parameters ()
 :precondition (and
(not (made p14))
(started o2)
)
 :effect (and
(made p14)
))
(:action make-product-p15
 :parameters ()
 :precondition (and
(not (made p15))
(started o8)
(started o13)
(started o28)
)
 :effect (and
(made p15)
))
(:action make-product-p16
 :parameters ()
 :precondition (and
(not (made p16))
(started o17)
(started o22)
)
 :effect (and
(made p16)
))
(:action make-product-p17
 :parameters ()
 :precondition (and
(not (made p17))
(started o3)
)
 :effect (and
(made p17)
))
(:action make-product-p18
 :parameters ()
 :precondition (and
(not (made p18))
(started o26)
)
 :effect (and
(made p18)
))
(:action make-product-p19
 :parameters ()
 :precondition (and
(not (made p19))
(started o1)
(started o24)
)
 :effect (and
(made p19)
))
(:action make-product-p20
 :parameters ()
 :precondition (and
(not (made p20))
(started o18)
)
 :effect (and
(made p20)
))
(:action make-product-p21
 :parameters ()
 :precondition (and
(not (made p21))
(started o14)
(started o21)
)
 :effect (and
(made p21)
))
(:action make-product-p22
 :parameters ()
 :precondition (and
(not (made p22))
(started o3)
(started o14)
(started o23)
)
 :effect (and
(made p22)
))
(:action make-product-p23
 :parameters ()
 :precondition (and
(not (made p23))
(started o5)
)
 :effect (and
(made p23)
))
(:action make-product-p24
 :parameters ()
 :precondition (and
(not (made p24))
(started o1)
)
 :effect (and
(made p24)
))
(:action make-product-p25
 :parameters ()
 :precondition (and
(not (made p25))
(started o15)
)
 :effect (and
(made p25)
))
(:action make-product-p26
 :parameters ()
 :precondition (and
(not (made p26))
(started o3)
)
 :effect (and
(made p26)
))
(:action make-product-p27
 :parameters ()
 :precondition (and
(not (made p27))
(started o26)
)
 :effect (and
(made p27)
))
(:action make-product-p28
 :parameters ()
 :precondition (and
(not (made p28))
(started o24)
)
 :effect (and
(made p28)
))
)
