package masproject;

import jade.core.Agent;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;

import org.json.JSONObject;

import java.io.FileWriter;

public class ReportAgent extends Agent {

    private static final String OUTPUT_PATH =
            "/home/reyhaneh.farahmand/SENG696_MAS/output/risk_report.json";

    @Override
    protected void setup() {
        System.out.println("ReportAgent started: " + getAID().getName());

        addBehaviour(new CyclicBehaviour() {
            @Override
            public void action() {
                ACLMessage msg = receive();
                if (msg == null) {
                    block();
                    return;
                }

                try {
                    JSONObject report = new JSONObject(msg.getContent());

                    try (FileWriter fw = new FileWriter(OUTPUT_PATH)) {
                        fw.write(report.toString(2));
                    }

                    System.out.println("[ReportAgent] Report saved → " + OUTPUT_PATH);

                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });
    }
}
