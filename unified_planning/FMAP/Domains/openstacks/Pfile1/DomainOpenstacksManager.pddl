(define (domain openstacks)
(:requirements :typing :equality :fluents)
(:types
    order product count - object)
(:constants
 p1 p2 p3 p4 p5 - product
 o1 o2 o3 o4 o5 - order
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
(:action start-order
 :parameters (?o - order ?avail ?new-avail - count)
 :precondition (and (waiting ?o) (= (stacks-avail) ?avail)
               (= (next-count ?new-avail) ?avail))
 :effect (and (not (waiting ?o)) (started ?o) (assign (stacks-avail) ?new-avail)))
(:action ship-order-o1
 :parameters (?avail ?new-avail - count)
 :precondition (and (= (stacks-avail) ?avail) (= (next-count ?avail) ?new-avail)
(started o1)
(made p2)
)
 :effect (and (assign (stacks-avail) ?new-avail)
(not 
(started o1)
)
(shipped o1)
))
(:action ship-order-o2
 :parameters (?avail ?new-avail - count)
 :precondition (and (= (stacks-avail) ?avail) (= (next-count ?avail) ?new-avail)
(started o2)
(made p1)
(made p2)
)
 :effect (and (assign (stacks-avail) ?new-avail)
(not 
(started o2)
)
(shipped o2)
))
(:action ship-order-o3
 :parameters (?avail ?new-avail - count)
 :precondition (and (= (stacks-avail) ?avail) (= (next-count ?avail) ?new-avail)
(started o3)
(made p3)
)
 :effect (and (assign (stacks-avail) ?new-avail)
(not 
(started o3)
)
(shipped o3)
))
(:action ship-order-o4
 :parameters (?avail ?new-avail - count)
 :precondition (and (= (stacks-avail) ?avail) (= (next-count ?avail) ?new-avail)
(started o4)
(made p3)
(made p4)
)
 :effect (and (assign (stacks-avail) ?new-avail)
(not 
(started o4)
)
(shipped o4)
))
(:action ship-order-o5
 :parameters (?avail ?new-avail - count)
 :precondition (and (= (stacks-avail) ?avail) (= (next-count ?avail) ?new-avail)
(started o5)
(made p5)
)
 :effect (and (assign (stacks-avail) ?new-avail)
(not 
(started o5)
)
(shipped o5)
))
)
