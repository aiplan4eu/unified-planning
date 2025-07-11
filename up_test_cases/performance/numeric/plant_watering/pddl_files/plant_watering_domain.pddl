;; Enrico Scala (enricos83@gmail.com) and Miquel Ramirez (miquel.ramirez@gmail.com)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Plant watering domain - metric-ff version
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; An agent on a grid-like map aims pos watering some plants by
;;; carrying water from a tap to the plants.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Adapted to do away with the grid (Enrico Scala & Miquel Ramirez, August 2015)
;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define (domain mt-plant-watering)
    (:requirements :strips :typing :numeric-fluents)
    (:types thing - object
        agent plant tap - thing)


    (:functions
        (maxx) ;; bounds
        (maxy) ;; bounds
        (miny) ;; bounds
        (minx) ;; bounds
        (x ?t - thing) ;; x coordinate of the location for ?t
        (y ?t - thing) ;; y coordinate of the location for ?t
        (carrying) ;; The amount of water carried by the agent.
        (poured ?p - plant) ;; The amount of water poured to the plant so far.
        (total_poured) ;; The total amount of water poured so far.
        (total_loaded) ;; The total amount of water retrieved from the tap.
        (max_int) ;; The maximum integer we consider - a static value
    )

    ;; Move an agent to a neighboring location
    (:action move_up
     :parameters (?a - agent)
     :precondition (and (<= (+ (y ?a) 1) (maxy)))
     :effect (and
    		(increase (y ?a) 1)))

    (:action move_down
     :parameters (?a - agent)
     :precondition (and (>= (- (y ?a) 1) (miny)))
     :effect (and
    		(decrease (y ?a) 1)))

    (:action move_right
     :parameters (?a - agent)
     :precondition (and (<= (+ (x ?a) 1) (maxx)))
     :effect (and
    		(increase (x ?a) 1)))

    (:action move_left
     :parameters (?a - agent)
     :precondition (and (>= (- (x ?a) 1) (minx)))
     :effect (and
    		(decrease (x ?a) 1)))

  (:action move_up_left
   :parameters (?a - agent)
   :precondition (and (>= (- (x ?a) 1) (minx)) (<= (+ (y ?a) 1) (maxy)))
   :effect (and
      (increase (y ?a) 1) (decrease (x ?a) 1)))

  (:action move_up_right
   :parameters (?a - agent)
   :precondition (and (<= (+ (x ?a) 1) (maxx)) (<= (+ (y ?a) 1) (maxy)))
   :effect (and
      (increase (y ?a) 1) (increase (x ?a) 1)))

  (:action move_down_left
   :parameters (?a - agent)
   :precondition (and (>= (- (x ?a) 1) (minx)) (>= (- (y ?a) 1) (miny)))
   :effect (and
      (decrease (x ?a) 1) (decrease (y ?a) 1) )
  )

(:action move_down_right
 :parameters (?a - agent)
 :precondition (and (<= (+ (x ?a) 1) (maxx)) (>= (- (y ?a) 1) (miny)))
 :effect (and
    (decrease (y ?a) 1) (increase (x ?a) 1)))

    ;; Load one unit of water from a tap into the agent's bucket.
    (:action load
    :parameters (?a - agent ?t - tap)
    :precondition (and (= (x ?a) (x ?t)) (=(y ?a) (y ?t))
                       (<= (+ (total_loaded) 1) (max_int))
                       (<= (+ (carrying) 1) (max_int))
                  )
    :effect       (and (increase (carrying) 1) (increase (total_loaded) 1))
    )

    ;; Pours one unit of water from the agent's bucket into a plant.
    (:action pour
    :parameters (?a - agent ?p - plant)
    :precondition (and (= (x ?a) (x ?p)) (=(y ?a) (y ?p))
                       (>= (carrying) 1)
                       (<= (+ (total_poured) 1) (max_int))
                       (<= (+ (poured ?p) 1) (max_int))
                  )
    :effect       (and
                    (decrease (carrying) 1)
                    (increase (poured ?p) 1)
                    (increase (total_poured) 1)
                  )
    )
)
