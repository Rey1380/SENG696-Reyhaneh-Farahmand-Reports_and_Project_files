package masproject;

import jade.core.AID;
import jade.core.Agent;
import jade.core.behaviours.OneShotBehaviour;
import jade.core.behaviours.SequentialBehaviour;
import jade.lang.acl.ACLMessage;

import org.json.JSONObject;

public class OrchestratorAgent extends Agent {

    @Override
    protected void setup() {
        System.out.println("OrchestratorAgent started: " + getAID().getName());

        addBehaviour(new OneShotBehaviour() {
            @Override
            public void action() {

                try {
                    String fileName = "aes_demo.c";
                    String code = "void aes_encrypt(unsigned char* in, unsigned char* out) { strcpy(in,out); }";

                    JSONObject req = new JSONObject();
                    req.put("file", fileName);
                    req.put("code", code);

                    // === STEP 1: SEND TO AiOriginAgent ===
                    ACLMessage msg = new ACLMessage(ACLMessage.REQUEST);
                    msg.addReceiver(new AID("ai-origin", AID.ISLOCALNAME));
                    msg.setContent(req.toString());
                    send(msg);

                    System.out.println("Orchestrator → AiOriginAgent");

                    // WAIT FOR RESPONSE 
                    ACLMessage resp = blockingReceive();
                    JSONObject aiResult = new JSONObject(resp.getContent());
                    System.out.println("Orchestrator ← AiOriginAgent: " + aiResult);

                    // STEP 2: SEND TO SeverityAgent 
                    ACLMessage sevMsg = new ACLMessage(ACLMessage.REQUEST);
                    sevMsg.addReceiver(new AID("severity", AID.ISLOCALNAME));
                    sevMsg.setContent(aiResult.toString());
                    send(sevMsg);

                    ACLMessage sevResp = blockingReceive();
                    JSONObject sevJson = new JSONObject(sevResp.getContent());

                    System.out.println("Orchestrator ← SeverityAgent: " + sevJson);

                    //  STEP 3: SEND FINAL TO REPORT AGENT 
                    ACLMessage repMsg = new ACLMessage(ACLMessage.REQUEST);
                    repMsg.addReceiver(new AID("report", AID.ISLOCALNAME));
                    repMsg.setContent(sevJson.toString());
                    send(repMsg);

                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });
    }
}
