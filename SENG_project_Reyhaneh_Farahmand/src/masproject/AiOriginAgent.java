package masproject;

import jade.core.Agent;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

import org.json.JSONObject;

public class AiOriginAgent extends Agent {

    @Override
    protected void setup() {
        System.out.println("AiOriginAgent started: " + getAID().getName());

        addBehaviour(new CyclicBehaviour() {
            @Override
            public void action() {
                ACLMessage msg = receive();
                if (msg == null) {
                    block();
                    return;
                }

                try {
                    JSONObject req = new JSONObject(msg.getContent());
                    String fileName = req.getString("file");
                    String code = req.getString("code");

                    String detectorResponse = callDetectorAPI(code);
                    JSONObject detJson = new JSONObject(detectorResponse);

                    String labelStr = detJson.optString("label", "Human");
                    int aiLabel = labelStr.equalsIgnoreCase("AI") ? 1 : 0;

                    System.out.println("[AiOriginAgent] → Returned AI label: " + aiLabel);

                    JSONObject out = new JSONObject();
                    out.put("file", fileName);
                    out.put("code", code);
                    out.put("ai_label", aiLabel);

                    ACLMessage reply = msg.createReply();
                    reply.setPerformative(ACLMessage.INFORM);
                    reply.setContent(out.toString());
                    send(reply);

                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });
    }


    private String callDetectorAPI(String code) throws Exception {
        URL url = new URL("http://127.0.0.1:8081/analyze");
        HttpURLConnection con = (HttpURLConnection) url.openConnection();
        con.setRequestMethod("POST");
        con.setRequestProperty("Content-Type", "application/json");
        con.setDoOutput(true);

        JSONObject payload = new JSONObject();
        payload.put("code", code);

        try (OutputStream os = con.getOutputStream()) {
            os.write(payload.toString().getBytes());
        }

        BufferedReader br = new BufferedReader(new InputStreamReader(con.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;

        while ((line = br.readLine()) != null) sb.append(line);

        return sb.toString();
    }
}
