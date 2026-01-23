using System;
using System.Collections.Generic;
using System.Linq;
using Environments;
using Google.Protobuf.Collections;
using Ik;
using NUnit;
using UnityEngine;
using Environment = Environments.Environment;
using Object = UnityEngine.Object;
using Quaternion = UnityEngine.Quaternion;
using Transform = UnityEngine.Transform;
using Vector3 = UnityEngine.Vector3;

namespace DefaultNamespace
{
    public class EnvironmentSpawner : MonoBehaviour
    {
        public GameObject cubeBowlPrefab;
        public GameObject trashPickingPrefab;
        public GameObject tablewarePrefab;
        public GameObject spheresPrefab;

        public int gridLength = 5;
        public int stepSize = 3;

        private Dictionary<int, EnvManager> envs = new();

        public static int defaultAgents = 1;
        public static Environment defaultEnvironment = Environment.EnvCubeBowl;

        public void DoAwake(RepeatedField<ResetParameters> resetMsgEnvsToReset)
        {
            ClearAgents();

            if (resetMsgEnvsToReset != null && resetMsgEnvsToReset.Count > 0)
            {
                SpawnAgents(resetMsgEnvsToReset);
            }
            else
            {
                SpawnAgents(Enumerable.Range(0, defaultAgents).ToList());
            }
        }

        private void SpawnAgents(List<int> agentIds)
        {
            var determinePrefab = DeterminePrefab(defaultEnvironment);
            foreach (var i in agentIds)
            {
                var instantiate = Instantiate(determinePrefab, new Vector3(stepSize * (i % gridLength), 0, gridLength * (i / gridLength)) * 2, Quaternion.identity);
                envs.Add(i, instantiate.GetComponent<EnvManager>());
                //TODO Should refactor to functional format
            }
        }


        private void SpawnAgents(RepeatedField<ResetParameters> envParameters)
        {
            List<int> agentIds = new();
            foreach (var resetParameters in envParameters)
            {
                int i = resetParameters.Index;
                var instantiate = Instantiate(DeterminePrefab(envParameters[i]), new Vector3(stepSize * (i % gridLength), 0, gridLength * (i / gridLength)) * 2, Quaternion.identity);
                envs.Add(i, instantiate.GetComponent<EnvManager>());
                
                agentIds.Add(i);
            }

            var remainingIds = Enumerable.Range(0, defaultAgents).Except(agentIds);
            SpawnAgents(remainingIds.ToList());
        }

        private GameObject DeterminePrefab(ResetParameters envParameter)
        {
            if (envParameter.EnvCubeBowl != null) return cubeBowlPrefab;
            if (envParameter.EnvTrashPicking != null) return trashPickingPrefab;
            if (envParameter.EnvTableware != null) return tablewarePrefab;
            if (envParameter.EnvSpheres != null) return spheresPrefab;
            return DeterminePrefab(defaultEnvironment);
        }

        private GameObject DeterminePrefab(Environment envParameter)
        {
            if (envParameter == Environment.EnvCubeBowl) return cubeBowlPrefab;
            if (envParameter == Environment.EnvTrashPicking) return trashPickingPrefab;
            if (envParameter == Environment.EnvTableware) return tablewarePrefab;
            if (envParameter == Environment.EnvSpheres) return spheresPrefab;
            return null;
        }

        public void SetLayer(GameObject go, int layer)
        {
            go.layer = layer;
            foreach (Transform child in go.transform)
            {
                child.gameObject.layer = layer;
                SetLayer(child.gameObject, layer);
            }
        }

        public void ClearAgents()
        {
            envs.Values.ToList().ForEach(manager => Destroy(manager.gameObject));
            envs = new Dictionary<int, EnvManager>();
        }

        private Bounds EncapsulateGameObjects(List<GameObject> gameObjects)
        {
            var mapBoundsHelper = gameObjects[0].GetComponent<Renderer>().bounds;
            foreach (GameObject renderer in gameObjects)
            {
                var rendererBounds = renderer.transform.GetComponent<Renderer>();
                if (rendererBounds != null)
                {
                    mapBoundsHelper.Encapsulate(rendererBounds.bounds);
                }
                else
                {
                    foreach (var componentsInChild in renderer.GetComponentsInChildren<Renderer>())
                    {
                        mapBoundsHelper.Encapsulate(componentsInChild.bounds);
                    }
                }
            }

            return mapBoundsHelper;
        }

        public static List<GameObject> FindAllChildrenWithComponent<T>(Transform item)
        {
            var objects = new List<GameObject>();
            foreach (Transform child in item)
            {
                if (item.GetComponent<T>() != null)
                {
                    objects.Add(child.gameObject);
                }

                objects.AddRange(FindAllChildrenWithComponent<T>(child));
            }

            return objects;
        }

        public Dictionary<int, EnvManager> GetEnvs()
        {
            return envs;
        }
    }
}