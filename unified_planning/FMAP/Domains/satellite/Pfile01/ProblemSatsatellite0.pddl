(define (problem strips-sat-x-1)
(:domain satellite)
(:objects
 satellite0 - satellite
 instrument0 - instrument
 image1 spectrograph2 thermograph0 - mode
 star0 groundstation1 groundstation2 phenomenon3 phenomenon4 star5 phenomenon6 - direction
)
(:init (mySatellite satellite0)
 (power_avail satellite0)
 (not (power_on instrument0))
 (not (calibrated instrument0))
 (= (calibration_target instrument0) groundstation2)
 (not (have_image phenomenon4 thermograph0))
 (not (have_image star5 thermograph0))
 (not (have_image phenomenon6 thermograph0))
 (= (pointing satellite0) phenomenon6)
 (= (on_board satellite0) {instrument0})
 (not (= (on_board satellite0) {}))
 (= (supports instrument0) {thermograph0})
 (not (= (supports instrument0) {image1 spectrograph2}))
)
(:global-goal (and
 (have_image phenomenon4 thermograph0)
 (have_image star5 thermograph0)
 (have_image phenomenon6 thermograph0)
))
)
