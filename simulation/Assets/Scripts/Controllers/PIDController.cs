using Ik;
using UnityEngine;
using UnityEngine.Serialization;

namespace Controllers
{
    public class PIDController : MonoBehaviour
    {
        [FormerlySerializedAs("Kp")] public float kp = 1;
        [FormerlySerializedAs("Kd")] public float kd = 1;
        [FormerlySerializedAs("Ki")] public float ki = 0;

        private float _previous;
        private float _integral;
        public float error;

        public float Iterate(float current)
        {
            error = current;
            var p = current;
            var d = current - _previous;
            if (ki != 0) _integral += current;
            _previous = current;
            return kp * p + kd * d + _integral * ki;
        }

        public void Reset()
        {
            _integral = 0;
            _previous = 0;
            error = 0;
        }

        public void SetParameters(PID pidParams)
        {
            kp = pidParams.Kp;
            kd = pidParams.Kd;
            ki = pidParams.Ki;
        }
    }
}