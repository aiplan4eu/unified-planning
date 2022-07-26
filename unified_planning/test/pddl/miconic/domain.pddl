(define (domain miconic)
  (:requirements :adl)
  (:types passenger - object
          floor - object
         )

(:predicates

(going_up ?person - passenger)
(going_down ?person - passenger)
(vip ?person - passenger)
(going_nonstop ?person - passenger)
(attendant ?person - passenger)
(never_alone ?person - passenger)
(conflict_A ?person - passenger)
(conflict_B ?person - passenger)

(origin ?person - passenger ?floor - floor)
;; entry of ?person is ?floor
;; inertia

(destin ?person - passenger ?floor - floor)
;; exit of ?person is ?floor
;; inertia

(no-access ?person - passenger ?floor - floor)
;; access limitation of ?person on ?floor

(above ?floor1 - floor  ?floor2 - floor)
;; ?floor2 is located above of ?floor1

(boarded ?person - passenger)
;; true if ?person has boarded the lift

(served ?person - passenger)
;; true if ?person has alighted as her destination

(lift-at ?floor - floor)
;; current position of the lift is at ?floor
)


;;stop

(:action
 stop
 :parameters (?f - floor)
 :precondition (and (lift-at ?f)
		    (imply
		     (exists (?p - passenger)
			     (and (conflict_A ?p)
				  (or (and (not (served ?p))
					   (origin ?p ?f))
				      (and (boarded ?p)
					   (not (destin ?p ?f))))))
		     (forall (?q - passenger)
			     (imply (conflict_B ?q)
				      (and (or (destin ?q ?f)
					       (not (boarded ?q)))
					   (or (served ?q)
					       (not (origin ?q ?f)))))))
		    (imply (exists (?p - passenger)
				   (and (conflict_B ?p)
					(or (and (not (served ?p))
						 (origin ?p ?f))
					    (and (boarded ?p)
						 (not (destin ?p ?f))))))
			   (forall (?q - passenger)
				   (imply (conflict_A ?q)
					    (and (or (destin ?q ?f)
						     (not (boarded ?q)))
						 (or (served ?q)
						     (not (origin ?q ?f)))))))
		    (imply
		     (exists (?p - passenger)
			     (and (never_alone ?p)
				  (or (and (origin ?p ?f)
					   (not (served ?p)))
				      (and (boarded ?p)
					   (not (destin ?p ?f))))))
		     (exists (?q - passenger)
			     (and (attendant ?q)
				  (or (and (boarded ?q)
					   (not (destin ?q ?f)))
				      (and (not (served ?q))
					   (origin ?q ?f))))))
		    (forall (?p - passenger)
			    (imply (going_nonstop ?p)
				   (imply (boarded ?p) (destin ?p ?f))))

		    (or (forall (?p - passenger)
				(imply (vip ?p) (served ?p)))
			(exists
			 (?p - passenger)
			 (and (vip ?p)
			      (or (origin ?p ?f) (destin ?p ?f)))))
		    (forall
		     (?p - passenger)
		     (imply
		      (no-access ?p ?f) (not (boarded ?p)))))
 :effect (and
	  (forall (?p - passenger)
                  (when (and (boarded ?p)
                             (destin ?p ?f))
                        (and (not (boarded ?p))
                             (served  ?p))))
	  (forall (?p - passenger)
		  (when (and (origin ?p ?f) (not (served ?p)))
			(boarded ?p)))))


;;drive up

(:action up
  :parameters (?f1 - floor ?f2 - floor)
  :precondition (and (lift-at ?f1) (above ?f1 ?f2)
                     (forall (?p - passenger)
			     (imply (going_down ?p)
				      (not (boarded ?p)))))
  :effect (and (lift-at ?f2) (not (lift-at ?f1))))


;;drive down

(:action down
  :parameters (?f1 - floor ?f2 - floor)
  :precondition (and (lift-at ?f1) (above ?f2 ?f1)
                     (forall (?p - passenger)
			     (imply (going_up ?p)
				      (not (boarded ?p)))))
  :effect (and (lift-at ?f2) (not (lift-at ?f1))))
)
