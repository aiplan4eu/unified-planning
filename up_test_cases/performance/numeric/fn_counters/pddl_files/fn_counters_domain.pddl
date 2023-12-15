;; Enrico Scala (enricos83@gmail.com) and Miquel Ramirez (miquel.ramirez@gmail.com)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; counters-ineq-rnd domain, functional strips version
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Same domain than counters-ineq, only the instances will differ, since the initial values are set randomly.

(define (domain fn-counters)
    ;(:requirements :strips :typing :equality :adl)
    (:types counter)

    (:functions
        (value ?c - counter);; - int  ;; The value shown in counter ?c
        (max_int);; -  int ;; The maximum integer we consider - a static value
    )

    ;; Increment the value in the given counter by one
    (:action increment
         :parameters (?c - counter)
         :precondition (and (<= (+ (value ?c) 1) (max_int)))
         :effect (and (increase (value ?c) 1))
    )

    ;; Decrement the value in the given counter by one
    (:action decrement
         :parameters (?c - counter)
         :precondition (and (>= (value ?c) 1))
         :effect (and (decrease (value ?c) 1))
    )
)
