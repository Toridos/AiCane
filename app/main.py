import argparse, time, sys
from core.config import load_config
from core.shutdown import register_shutdown
from core.controller import Controller
from core.odom import Odom
from core.fsm import FSM, Mode
from perception.perceive import Perceiver
from perception.fusion import Fusion
from drivers.lidar_x4pro import LidarX4Pro
from drivers.serial_uno import SerialUNO
from planning.goal_biased import GoalBiasedPlanner
from planning.navigator import Navigator
from core.safety import SafetySystem

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['goal','mission'], default='goal')
    parser.add_argument('--goal', type=str, default='config/navigate_goal.yaml')
    parser.add_argument('--mission', type=str, default='config/mission.yaml')
    args = parser.parse_args()

    cfg = load_config('config/default.yaml')
    register_shutdown()

    # Hardware links
    uno = SerialUNO(cfg['serial']['port'], cfg['serial']['baudrate'])
    controller = Controller(uno)
    lidar = LidarX4Pro(port=cfg['lidar']['port'])
    perceiver = Perceiver(cfg)
    fusion = Fusion(lidar=lidar, perceiver=perceiver, estop_front=cfg['safety']['estop_front_m'])

    # Odometry (no-IMU, kv/kw calibrated)
    odom = Odom(kv=cfg['odom']['kv'], kw=cfg['odom']['kw'])

    # Planner selection
    if args.mode == 'goal':
        goal_cfg = load_config(args.goal)
        planner = GoalBiasedPlanner(**goal_cfg.get('planner', {}))
        goal_xy = (goal_cfg['goal']['x'], goal_cfg['goal']['y'])
        fsm = FSM(mode=Mode.FOLLOW_GOAL, planner=planner, controller=controller, fusion=fusion, odom=odom, goal_xy=goal_xy)
    else:
        mission = load_config(args.mission)
        from planning.navigator import Navigator
        navi = Navigator(mission=mission, lookahead=0.6)
        fsm = FSM(mode=Mode.FOLLOW_MISSION, planner=navi, controller=controller, fusion=fusion, odom=odom)

    safety = SafetySystem(controller=controller)

    print("[SYSTEM] AiCane Project Planner Started – mode:", args.mode)
    v_cmd_last = 0.0; w_cmd_last = 0.0

    try:
        while True:
            # Update sensors / perception
            frame = perceiver.get_frame()
            fusion.update_cache(frame)

            # FSM tick → (v_mps, steer_deg, mode)
            v_cmd, steer_deg, mode = fsm.tick()

            # Safety rules
            if fusion.emergency_stop():
                v_cmd, steer_deg = 0.0, 0.0

            # Send to UNO (speed, steer)
            controller.send_speed_steer(v_cmd, steer_deg)

            # Odometry integration (command-integrated odom)
            odom.step(v_cmd_mps=v_cmd, w_cmd_dps=controller.deg_per_sec_from_steer(steer_deg))

            v_cmd_last, w_cmd_last = v_cmd, controller.deg_per_sec_from_steer(steer_deg)

            safety.check_heartbeat()

            time.sleep(0.05)  # ~20 Hz
    except KeyboardInterrupt:
        controller.stop_all()
        print("\n[SYSTEM] Stopped.")
    finally:
        perceiver.shutdown()
        uno.close()

if __name__ == '__main__':
    main()
